#!/bin/bash                                                                     

# Note: Mininet must be run as root.  So invoke this shell script               
# using sudo.                                                                   

time=60
bwnet=100
# TODO: If you want the RTT to be 20ms what should the delay on each            
# link be?  Set this value correctly.                                           
delay=7.5
dir=output
iperf_port=5001

for qsize in 5 10 15 20 25 30 35 40 45 50 60 70 80 90 100 110 120 130 140 150 160 170 180 190 200 225 250 275; do

    # PCC and corresponding plots                                               
    python small-queue.py -b $bwnet -t $time --delay $delay  --maxq $qsize --dir $dir --algo pcc
    python plot_queue.py -f $dir/PCC/$qsize-q.txt -o $dir/PCC/$qsize-q.png


    # TCP cubic and corresponding plots                                         
    python small-queue.py -b $bwnet -t $time --delay $delay  --maxq $qsize --dir $dir --algo cubic
    python plot_tcpprobe.py -f $dir/TCP/$qsize-cwnd.txt -o $dir/TCP/$qsize-cwnd-iperf.png -p $iperf_port
    python plot_queue.py -f $dir/TCP/$qsize-q.txt -o $dir/TCP/$qsize-q.png


done

python plot_throughputs.py
