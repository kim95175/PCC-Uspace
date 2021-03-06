
#include "pcc_python_rc.h"
#include <algorithm>
#include <iostream>
using namespace std;

std::mutex PccPythonRateController::interpreter_lock_;
bool PccPythonRateController::python_initialized_ = false;

void PccPythonRateController::InitializePython() {
    Py_Initialize();
    PyRun_SimpleString("import sys");

    std::stringstream set_argv_ss;
    set_argv_ss << "sys.argv = [";
    wchar_t** unicode_args = new wchar_t*[Options::argc];
    for (int i = 0; i < Options::argc; ++i) {
        const char* arg = Options::argv[i];
        if (i == 0) {
            set_argv_ss << "\"" << arg << "\"";
        } else {
            set_argv_ss << ", \"" << arg << "\"";
        }
        int len = strlen(arg);
        std::wstring wc(len, L'#' );
        mbstowcs(&wc[0], arg, len);
        unicode_args[i] = &wc[0];
    }
    set_argv_ss << "]";
    std::string set_argv_str = set_argv_ss.str();
    PyRun_SimpleString(set_argv_str.c_str());

    python_initialized_ = true;
}

int PccPythonRateController::GetNextId() {
    
    static int next_id = 0;
    int id = next_id;
    ++next_id;
    return id;
    /*static int next_id = id;
    int r_id = next_id;
    ++next_id;
    return r_id;*/
    
}

PccPythonRateController::PccPythonRateController(double call_freq,
        PccEventLogger* log) {

    std::lock_guard<std::mutex> lock(interpreter_lock_);
    //std::cerr << "[python_rc]PccPythonRateController lock on " << std::endl;
    if (!python_initialized_) {
        InitializePython();
    }
    
    id = GetNextId();
    has_time_offset = false;
    time_offset_usec = 0;

    const char* python_path_arg = Options::Get("-pypath="); // The location in which the pcc_addon.py file can be found.
    python_path_arg = "/home/airman/Github/cc-gym/src/udt-plugins/testing/";
    //python_path_arg = "/home/airman/Github/cc-gym/src/udt-plugins/training/"

    if (python_path_arg != NULL) {
        cout << "pypath: " << python_path_arg << endl;
        int python_path_arg_len = strlen(python_path_arg);
        char python_path_cmd_buf[python_path_arg_len + 50];
        sprintf(&python_path_cmd_buf[0], "sys.path.append(\"%s\")", python_path_arg);
        PyRun_SimpleString(&python_path_cmd_buf[0]);
        //std::cerr << "Adding python path: " << python_path_arg << std::endl;
    }

    const char* python_filename = "pcc_rate_controller";
    const char* python_filename_arg = Options::Get("-pyhelper=");
    python_filename_arg = "loaded_client";
    //python_filename_arg = "shim"
    

    if (python_filename_arg != NULL) {
        cout << "pyhelper: " << python_filename_arg << endl;
        cerr << "pyhelper: " << python_filename_arg << endl;
        python_filename = python_filename_arg;
    }
    
    module = PyImport_ImportModule(python_filename);
    if (module == NULL) {
        std::cerr << "ERROR: Could not load python module: " << python_filename << std::endl;
        PyErr_Print();
        exit(-1);
    }
    
    PyObject* init_func = PyObject_GetAttrString(module, "init");
    if (init_func == NULL) {
        std::cerr << "ERROR: Could not load python function: init" << std::endl;
        PyErr_Print();
        exit(-1);
    }
    PyObject* id_obj = PyLong_FromLong(id);
    static PyObject* args = PyTuple_New(1);
    PyTuple_SetItem(args, 0, id_obj);
    
    PyObject* init_result = PyObject_CallObject(init_func, args);
    PyErr_Print();
    
    give_sample_func = PyObject_GetAttrString(module, "give_sample");
    if (give_sample_func == NULL) {
        std::cerr << "ERROR: Could not load python function: give_sample" << std::endl;
        PyErr_Print();
        exit(-1);
    }
    
    get_rate_func = PyObject_GetAttrString(module, "get_rate");
    if (get_rate_func == NULL) {
        std::cerr << "ERROR: Could not load python function: get_rate" << std::endl;
        PyErr_Print();
        exit(-1);
    }
    
    reset_func = PyObject_GetAttrString(module, "reset");
    if (reset_func == NULL) {
        std::cerr << "ERROR: Could not load python function: reset" << std::endl;
        PyErr_Print();
        exit(-1);
    }
}

void PccPythonRateController::Reset() {
    std::cout << "Starting Reset" << std::endl;
    std::lock_guard<std::mutex> lock(interpreter_lock_);
    std::cerr << "[python_rc]Reset lock on " << std::endl;
    PyObject* id_obj = PyLong_FromLong(id);
    static PyObject* args = PyTuple_New(1);
    PyTuple_SetItem(args, 0, id_obj);
    
    PyObject* result = PyObject_CallObject(reset_func, args);
    PyErr_Print();
}

/*void PccPythonRateController::GiveSample(int bytes_sent,
                                         int bytes_acked,
                                         int bytes_lost,
                                         double send_start_time_sec,
                                         double send_end_time_sec,
                                         double recv_start_time_sec,
                                         double recv_end_time_sec,
                                         double first_ack_latency_sec,
                                         double last_ack_latency_sec,
                                         int packet_size,
                                         double utility) */

//double PccPythonRateController::GiveSample(int bytes_sent,
void PccPythonRateController::GiveSample(int bytes_sent,
                                         int bytes_acked,
                                         int bytes_lost,
                                         double send_start_time_sec,
                                         double send_end_time_sec,
                                         double recv_start_time_sec,
                                         double recv_end_time_sec,
                                         double first_ack_latency_sec,
                                         double last_ack_latency_sec,
                                         int packet_size,
                                         double utility) {

    std::lock_guard<std::mutex> lock(interpreter_lock_);
    std::cerr << "[python_rc]GiveSample lock on " << std::endl;
    static PyObject* args = PyTuple_New(12);
    //static PyObject* args = PyTuple_New(11);
    
    // flow_id
    PyTuple_SetItem(args, 0, PyLong_FromLong(id));
    
    // bytes_sent
    PyTuple_SetItem(args, 1, PyLong_FromLong(bytes_sent));
    
    // bytes_acked
    PyTuple_SetItem(args, 2, PyLong_FromLong(bytes_acked));
    
    // bytes_lost
    PyTuple_SetItem(args, 3, PyLong_FromLong(bytes_lost));
    
    // send_start_time
    PyTuple_SetItem(args, 4, PyFloat_FromDouble(send_start_time_sec));
    
    // send_end_time
    PyTuple_SetItem(args, 5, PyFloat_FromDouble(send_end_time_sec));
    
    // recv_start_time
    PyTuple_SetItem(args, 6, PyFloat_FromDouble(recv_start_time_sec));
    
    // recv_end_time
    PyTuple_SetItem(args, 7, PyFloat_FromDouble(recv_end_time_sec));

    //first_ack_rtt 
    PyTuple_SetItem(args, 8, PyFloat_FromDouble(first_ack_latency_sec));

    //last_ack_rtt 
    PyTuple_SetItem(args, 9, PyFloat_FromDouble(last_ack_latency_sec));

    // packet_size
    PyTuple_SetItem(args, 10, PyLong_FromLong(packet_size));
    
    // recv_end_time
    PyTuple_SetItem(args, 11, PyFloat_FromDouble(utility));
    
    std::cerr << " Call Object give_sample_func" << std::endl;
    PyObject_CallObject(give_sample_func, args);
    std::cerr << " id : " << id << std::endl; 
    
    /*
    PyObject* id_obj = PyLong_FromLong(id);
    static PyObject* rate_args = PyTuple_New(1);
    PyTuple_SetItem(rate_args, 0, id_obj);
    
    std::cerr << " Call Object get_rate_func" << std::endl;
    PyObject* result = PyObject_CallObject(get_rate_func, rate_args);
    if (result == NULL) {
        std::cerr << "ERROR: Failed to call python get_rate() func" << std::endl;
        std::cout << "ERROR: Failed to call python get_rate() func" << std::endl;
        PyErr_Print();
        exit(-1);
    }
    double result_double = PyFloat_AsDouble(result);
    PyErr_Print();
    if (!PyFloat_Check(result)) {
        std::cerr << "ERROR: Failed to call python get_rate() func" << std::endl;
        std::cout << "ERROR: Output from python get_rate() is not a float" << std::endl;
        exit(-1);
    }
    Py_DECREF(result);
    std::cerr << " result Rate : " << result_double << std::endl;
    std::cerr << "[python_rc]GiveSample lock off " << std::endl;
    return result_double;*/
}



void PccPythonRateController::MonitorIntervalFinished(const MonitorInterval& mi) {
//double PccPythonRateController::MonitorIntervalFinished(const MonitorInterval& mi) {
    
    /*if (!has_time_offset) {
        set_usec = mi.GetSendStartTime();
        has_time_offset = true;
    }*/
    time_offset_usec = mi.GetSendStartTime();
    //double result = GiveSample(  mi.GetBytesSent(),
    GiveSample( mi.GetBytesSent(),
        mi.GetBytesAcked(),
        mi.GetBytesLost(),
        (mi.GetSendStartTime() - time_offset_usec) / (double)USEC_PER_SEC,
        (mi.GetSendEndTime() - time_offset_usec) / (double)USEC_PER_SEC,
        (mi.GetRecvStartTime() - time_offset_usec) / (double)USEC_PER_SEC,
        (mi.GetRecvEndTime() - time_offset_usec) / (double)USEC_PER_SEC,
        mi.GetFirstAckLatency() / (double)USEC_PER_SEC,
        mi.GetLastAckLatency() / (double)USEC_PER_SEC,
        mi.GetAveragePacketSize(),
        mi.GetUtility()
    );
    //return result;
}

QuicBandwidth PccPythonRateController::GetNextSendingRate(QuicBandwidth current_rate, QuicTime cur_time) {

    std::cerr << "[python_rc]start GetNextSendingRate" << std::endl;
    std::lock_guard<std::mutex> lock(interpreter_lock_);
    std::cerr << "[python_rc]GetNextSendingRate lock on" << std::endl;
    PyObject* id_obj = PyLong_FromLong(id);
    static PyObject* args = PyTuple_New(1);
    PyTuple_SetItem(args, 0, id_obj);
    
    PyObject* result = PyObject_CallObject(get_rate_func, args);
    std::cerr << "rate_result " << result << std::endl;
    if (result == NULL) {
        std::cerr << "ERROR: Failed to call python get_rate() func" << std::endl;
        std::cerr << "ERROR: Failed to call python get_rate() func" << std::endl;
        PyErr_Print();
        exit(-1);
    }
    
    double result_double = PyFloat_AsDouble(result);
    std::cerr << "rate_delta " << result_double << std::endl;
    PyErr_Print();
    if (!PyFloat_Check(result)) {
        std::cerr << "ERROR: Failed to call python get_rate() func" << std::endl;
        std::cerr << "ERROR: Output from python get_rate() is not a float" << std::endl;
        exit(-1);
    }
    Py_DECREF(result);
    //std::cerr << " result Rate : " << result_double << std::endl;
    return result_double;
}
