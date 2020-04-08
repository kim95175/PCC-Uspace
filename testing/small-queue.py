# Topology for replicating figure 7 in the PCC paper

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.cli import CLI

from subprocess import Popen, PIPE
from argparse import ArgumentParser
from monitor import monitor_qlen
from multiprocessing import Process

import sys
import os
import threading
from time import sleep, time

parser = ArgumentParser(description="Shallow queue tests")

parser.add_argument('--bw-net', '-b',
                    type=float,
                    help="Bandwidth of bottleneck (network) link (Mb/s)",
                    required=True)

parser.add_argument('--delay',
                    type=float,
                    help="Link propagation delay (ms)",
                    required=True)

parser.add_argument('--dir', '-d',
                    help="Directory to store outputs",
                    required=True)

parser.add_argument('--time', '-t',
                    help="Duration (sec) to run the experiment",
                   type=int,
                    default=10)

parser.add_argument('--maxq',
                    type=int,
                    help="Max buffer size of network interface in packets",
                    required=True)

parser.add_argument('--algo',
                    help="Algorithm under which we are running the simulation",
                    required=True) 


args = parser.parse_args()

class ShallowQueueTopo(Topo):
    '''
    Single switch connecting a sender and receiver with a small 
    queue
    '''
    def build(self, n=2):
        switch = self.addSwitch('s0')
        h1linkopts = {'bw':1000, 'delay': str(args.delay) + 'ms', 'use_htb':True}
        h2linkopts = {'bw':args.bw_net, 'delay': str(args.delay) + 'ms', 'use_htb':True, 
                      'max_queue_size':args.maxq}
        host1 = self.addHost('sender')
        host2 = self.addHost('receiver')
        self.addLink(host1, switch, **h1linkopts)
        self.addLink(host2, switch, **h2linkopts)
        

def RunPCC(net):
    receiver_pid = start_pcc_receiver(net)
    sender_pid = start_pcc_sender(net, receiver_pid)

def RunTCP(net, algo):

    start_tcp_server(net)
 
    start_tcp_client(net, algo)


def simpleRun():
    print "Queue Size is %d" % args.maxq
    if not os.path.exists(args.dir):
        os.makedirs(args.dir)
    if not os.path.exists(args.dir + "/TCP"):
        os.makedirs(args.dir + "/TCP")
    if not os.path.exists(args.dir + "/PCC"):
        os.makedirs(args.dir + "/PCC")
    if not os.path.exists(args.dir + "/TCP_RENO"):
        os.makedirs(args.dir + "/TCP_RENO")

    if args.algo == 'cubic':
        os.system("sysctl -w net.ipv4.tcp_congestion_control=cubic")
    elif args.algo == 'reno':
        os.system("sysctl -w net.ipv4.tcp_congestion_control=reno")
 
    topo = ShallowQueueTopo()
    net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink)
    net.start()
    if args.algo  == 'pcc':
         qmon = start_qmon(iface='s0-eth2',
                           outfile='%s/PCC/%s-q.txt' % (args.dir, str(args.maxq)))
         RunPCC(net)
         qmon.terminate();

    elif args.algo == 'cubic':

        start_tcpprobe("cwnd.txt")
        qmon = start_qmon(iface='s0-eth2',
                          outfile='%s/TCP/%s-q.txt' % (args.dir, str(args.maxq)))
        RunTCP(net, "cubic")
        qmon.terminate();
        stop_tcpprobe()

    elif args.algo == 'reno':
        start_tcpprobe("cwnd.txt")
        qmon = start_qmon(iface='s0-eth2',
                          outfile='%s/TCP_RENO/%s-q.txt' % (args.dir, str(args.maxq)))
        RunTCP(net, "reno")
        qmon.terminate();
        stop_tcpprobe()


    net.stop()

# Probing for congestion window plots
def start_tcpprobe(outfile="cwnd.txt"):
    os.system("rmmod tcp_probe; modprobe tcp_probe full=1;")
    sleep(1)
    if args.algo == 'cubic':
        Popen("cat /proc/net/tcpprobe > %s/TCP/%s-%s" % (args.dir, str(args.maxq), outfile),
              shell=True)
    elif args.algo == 'reno':
        Popen("cat /proc/net/tcpprobe > %s/TCP_RENO/%s-%s" % (args.dir, str(args.maxq), outfile),
              shell=True)

def stop_tcpprobe():
    Popen("killall -9 cat", shell=True).wait()
                     
def start_qmon(iface, interval_sec=0.1, outfile="q.txt"):
    monitor = Process(target=monitor_qlen,
                      args=(iface, interval_sec, outfile))
    monitor.start()
    return monitor

# Starts an appserver
def start_pcc_receiver(net):
    '''
    Begin PCC sender on host 1
    '''
    h2 = net.get('receiver')
    h2.cmdPrint('echo 4; echo 5; echo 6')
    h2.cmdPrint('export LD_LIBRARY_PATH=pcc/receiver/src; echo $LD_LIBRARY_PATH')
    pid = h2.cmd("./pcc/receiver/app/appserver 2> monitor_receiver.log &")
    sleep(1)
    print("Receiver started")
    return pid


# Starts an appclient
def start_pcc_sender(net, receiver_pid):
    '''
    Begin PCC receiver on host 2
    '''
    h1 = net.get('sender')
    h2 = net.get('receiver')
    h1.cmdPrint("export LD_LIBRARY_PATH=pcc/sender/src; echo $LD_LIBRARY_PATH")
    print("sender export")
    pid = h1.cmd("./pcc/sender/app/appclient " + h2.IP() + " 9000 > "  + args.dir 
                  + "/PCC/" + str(args.maxq)  + ".log &");
    print("Begin " + str(args.time) + " seconds of PCC transmission")
    sleep(args.time)

    h2.cmd("ps | pgrep -f appserver | xargs kill -9")
    h1.cmd("ps | pgrep -f appclient | xargs kill -9")
    sleep(1)
    return pid

# Starts an iperf server
def start_tcp_server(net):
    receiver = net.get('receiver')
    print("Starting server")
    receiver.popen('iperf -s -w 16m')
    print("Server started")
    sleep(1)

# Starts an iperf client
def start_tcp_client(net, algo):
    sender = net.get('sender')
    receiver = net.get('receiver')
    print("Starting receiver for " + str(args.time) + " seconds")
    if algo == "reno":
        client = sender.cmd("iperf -c " + receiver.IP() + " -t " + str(args.time) + " > " + args.dir 
                              + "/TCP_RENO/" + str(args.maxq)  + ".log");
    else:
        print("Running cubic iperf now")
        client = sender.cmd("iperf -c " + receiver.IP() + " -t " + str(args.time) + " > " + args.dir 
                              + "/TCP/" + str(args.maxq)  + ".log")

    print("Receiver started")
    sleep(args.time)
                

if __name__ == '__main__':
    simpleRun()
