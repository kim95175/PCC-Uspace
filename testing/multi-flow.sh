#!/bin/bash

# Note: Mininet must be run as root.  So invoke this shell script
# using sudo.

offset=500
bw_inner=100
bw_outer=1000
num_hosts=4
flow_time=2000
dir=logs_new


python multi-flow.py -B $bw_outer -b $bw_inner --offset $offset --num-hosts $num_hosts -d $dir --flow-time $flow_time
python multi-flow-PCC.py -B $bw_outer -b $bw_inner --offset $offset --num-hosts $num_hosts -d $dir
python multi-flow-plot.py --num-hosts $num_hosts -d $dir --offset $offset --flow-time $flow_time
#python calculate-fairness.py --num-hosts $num_hosts -d $dir --offset $offset --flow-time $flow_time
