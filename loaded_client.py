# Copyright 2019 Nathan Jay and Noga Rotman
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import inspect
import os
import random
import sys

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
grandparentdir = os.path.dirname(parentdir)
sys.path.insert(0, parentdir)
sys.path.insert(0, grandparentdir)
    
from common import sender_obs
from common.simple_arg_parse import arg_or_default
import loaded_agent

if not hasattr(sys, 'argv'):
    sys.argv  = ['']

MIN_RATE = 0.5
MAX_RATE = 300.0
DELTA_SCALE = 0.05

RESET_RATE_MIN = 5.0
RESET_RATE_MAX = 100.0

RESET_RATE_MIN = 6.0
RESET_RATE_MAX = 6.0

DEFAULT_MODEL = "/home/airman/Github/cc-gym/src/pcc_saved_models/model_paper/"
MODEL_PATH = arg_or_default("--model-path", DEFAULT_MODEL)

print("#" * 20)
print("Model ", DEFAULT_MODEL)
print("#" * 20)

for arg in sys.argv:
    arg_str = "NULL"
    try:
        arg_str = arg[arg.rfind("=") + 1:]
    except:
        pass

    if "--reset-target-rate=" in arg:
        RESET_RATE_MIN = float(arg_str)
        RESET_RATE_MAX = float(arg_str)

class PccGymDriver():
    
    flow_lookup = {}
    
    def __init__(self, flow_id):
        global RESET_RATE_MIN
        global RESET_RATE_MAX

        self.id = flow_id

        self.rate = random.uniform(RESET_RATE_MIN, RESET_RATE_MAX)
        self.history_len = arg_or_default("--history-len", 10)
        self.features = arg_or_default("--input-features",
                                       default="sent latency inflation,"
                                             + "latency ratio,"
                                             + "send ratio").split(",")
        self.history = sender_obs.SenderHistory(self.history_len,
                                                self.features,
                                                self.id)
        self.got_data = False

        self.agent = loaded_agent.LoadedModelAgent(MODEL_PATH)
        self.log = open("/home/airman/Github/cc-gym/sample_log.txt", 'w')
        self.log.write(str(flow_id))
        self.log.close()

        PccGymDriver.flow_lookup[flow_id] = self

    def get_rate(self):
        if self.has_data():
            #with open("/home/airman/Github/cc-gym/sample_log.txt", "a") as f:
            #    f.write("[driver.get_rate_func]\n")
            #    f.write("{}\n".format( (self.history.as_array()).tolist()) )
            rate_delta = self.agent.act(self.history.as_array())
            self.rate = apply_rate_delta(self.rate, rate_delta)
        return self.rate * 1e6

    def has_data(self):
        return self.got_data

    def set_current_rate(self, new_rate):
        self.current_rate = new_rate

    def record_observation(self, new_mi):
        self.history.step(new_mi)
        self.got_data = True

    def reset_rate(self):
        self.current_rate = random.uniform(RESET_RATE_MIN, RESET_RATE_MAX)

    def reset_history(self):
        self.history = sender_obs.SenderHistory(self.history_len,
                                                self.features,
                                                self.id)
        self.got_data = False

    def reset(self):
        self.agent.reset()
        self.reset_rate()
        self.reset_history()


    def give_sample(self, bytes_sent, bytes_acked, bytes_lost,
                    send_start_time, send_end_time, recv_start_time,
                    recv_end_time, first_rtt, last_rtt, packet_size, utility):
        rtt_samples = [first_rtt, last_rtt]
        #print(rtt_samples)
        '''
        with open("/home/airman/Github/cc-gym/sample_log.txt", "a") as f:
            f.write("[driver.give_sample]\n flow_id : {}\n, bytes_sent : {}\n, bytes_acked : {}\n, bytes_lost : {}\n, send_start_time : {}\n, send_end_time : {}\n, recv_start_time : {}\n, recv_end_time : {}\n, first_rtt : {}\n, last_rtt : {}\n, packet_size : {}\n".format(self.id, bytes_sent, bytes_acked, bytes_lost, send_start_time, send_end_time, recv_start_time, recv_end_time, first_rtt, last_rtt, packet_size))
        '''
        self.record_observation(
            sender_obs.SenderMonitorInterval(
                self.id,
                bytes_sent=bytes_sent,
                bytes_acked=bytes_acked,
                bytes_lost=bytes_lost,
                send_start=send_start_time,
                send_end=send_end_time,
                recv_start=recv_start_time,
                recv_end=recv_end_time,
                rtt_samples=rtt_samples,
                #rtt_samples=[first_rtt, last_rtt],
                packet_size=packet_size
            )
        )
 
    def get_by_flow_id(flow_id):
        return PccGymDriver.flow_lookup[flow_id]

def give_sample(flow_id, bytes_sent, bytes_acked, bytes_lost,
                send_start_time, send_end_time, recv_start_time,
                recv_end_time, first_rtt, last_rtt, packet_size, utility):
    driver = PccGymDriver.get_by_flow_id(flow_id)
    driver.give_sample(bytes_sent, bytes_acked, bytes_lost,
                       send_start_time, send_end_time, recv_start_time,
                       recv_end_time, first_rtt, last_rtt, packet_size, utility)
    '''
    with open("/home/airman/Github/cc-gym/sample_log.txt", "a") as f:
        f.write("give_sample_func\n")
        driver = PccGymDriver.get_by_flow_id(flow_id)
        f.write("2\n")
        driver.give_sample(bytes_sent, bytes_acked, bytes_lost,
                       send_start_time, send_end_time, recv_start_time,
                       recv_end_time, first_rtt, last_rtt, packet_size, utility)
        f.write("3\n")
    '''

def apply_rate_delta(rate, rate_delta):
    global MIN_RATE
    global MAX_RATE
    global DELTA_SCALE
    
    rate_delta *= DELTA_SCALE

    # We want a string of actions with average 0 to result in a rate change
    # of 0, so delta of 0.05 means rate * 1.05,
    # delta of -0.05 means rate / 1.05
    if rate_delta > 0:
        rate *= (1.0 + rate_delta)
    elif rate_delta < 0:
        rate /= (1.0 - rate_delta)
    
    # For practical purposes, we may have maximum and minimum rates allowed.
    '''
    if rate < MIN_RATE:
        rate = MIN_RATE
    if rate > MAX_RATE:
        rate = MAX_RATE
    '''
    return rate
    #return MAX_RATE
    
def reset(flow_id):
    driver = PccGymDriver.get_by_flow_id(flow_id)
    driver.reset()

def get_rate(flow_id):
    #print("Getting rate")
    driver = PccGymDriver.get_by_flow_id(flow_id)
    return driver.get_rate()

def init(flow_id):
    driver = PccGymDriver(flow_id)