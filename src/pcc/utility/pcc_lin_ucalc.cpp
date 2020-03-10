
#include "pcc_lin_ucalc.h"
#include <cmath>
#define USEC_PER_SEC 1000000

namespace {
// Coefficeint of the loss rate term in utility function.
const float kLossCoefficient = 5.0f;
// Coefficient of RTT term in utility function.
const float kRttCoefficient = 1.0/30000.0f;
}  // namespace

float PccLinearUtilityCalculator::CalculateUtility(PccMonitorIntervalAnalysisGroup& past_monitor_intervals,
        MonitorInterval& cur_mi) {
  
  float throughput = cur_mi.GetObsThroughput();
  float avg_rtt = cur_mi.GetObsRtt() / 1000.0; //ms
  float loss_rate = cur_mi.GetObsLossRate();
  double first_rtt = cur_mi.GetFirstAckLatency() / 1000000.0;
  double last_rtt = cur_mi.GetLastAckLatency() / 1000000.0;
 /*
  if (loss_rate < 1.0) {
      last_rtt = avg_rtt;
  } else {
      avg_rtt = last_rtt;
  }*/

  float thpt_pkt_per_sec = throughput / (8.0 * 1500);
  float rtt_sec = avg_rtt / 1000000.0;

  float utility = pow(throughput, 0.9) - 1000 * avg_rtt - 11.35 * throughput * loss_rate;
  //utility = throughput - 1000 * avg_rtt - 1e8 * loss_rate;
  utility = 10.0 * thpt_pkt_per_sec - 1000.0 * rtt_sec - 2000.0 * loss_rate;
  uint64_t time_offset_usec = cur_mi.GetSendStartTime();

  //std::cout << "LINEAR CALC! Rtt: " << rtt_sec << std::endl;
  std::cout << "first Rtt: " << first_rtt << std::endl;
  std::cout << "last Rtt: " << last_rtt << std::endl;

  //utility = -1 * abs(cur_mi.GetObsSendingRate() - 1e7);

  PccLoggableEvent event("Calculate state", "--log-utility-calc-lite");
  event.AddValue("Utility", utility);
  event.AddValue("Bytes Sent", cur_mi.GetBytesSent());
  event.AddValue("Bytes Acked", cur_mi.GetBytesAcked());
  event.AddValue("Bytes Lost", cur_mi.GetBytesLost());
  event.AddValue("Send Start Time", (cur_mi.GetSendStartTime() - time_offset_usec) / (double)USEC_PER_SEC);
  event.AddValue("Send End Time", (cur_mi.GetSendEndTime() - time_offset_usec) / (double)USEC_PER_SEC) ;
  event.AddValue("Recv Start Time", (cur_mi.GetRecvStartTime() - time_offset_usec) / (double)USEC_PER_SEC) ;
  event.AddValue("Recv End Time", (cur_mi.GetRecvEndTime() - time_offset_usec) / (double)USEC_PER_SEC) ;
  event.AddValue("First Ack Latency", (cur_mi.GetFirstAckLatency() / (double)USEC_PER_SEC));
  event.AddValue("Last Ack Latency", (cur_mi.GetLastAckLatency() / (double)USEC_PER_SEC));
  event.AddValue("Target Rate", (cur_mi.GetTargetSendingRate() / (double)USEC_PER_SEC));
  event.AddValue("Actual Rate", (cur_mi.GetObsSendingRate() / (double)USEC_PER_SEC));
  event.AddValue("Throughput", throughput);
  event.AddValue("Loss Rate", loss_rate);
  event.AddValue("Avg RTT", avg_rtt);
  event.AddValue("Rtt_sample size", cur_mi.GetRTTSize());
  log->LogEvent(event);

  return utility;
}
