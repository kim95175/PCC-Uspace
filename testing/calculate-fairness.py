import matplotlib.pyplot as plt
import numpy as np

from argparse import ArgumentParser

parser = ArgumentParser(description="Multiflow tests")

parser.add_argument('--dir', '-d',
                    help="Directory to store outputs",
                    default='logs_new')

parser.add_argument('--flow-time', '-t',
                    help="Duration of each flow",
                    type=int,
                    default=400)

parser.add_argument('--offset',
                    help="Offset of the beginning of the next flow",
                    type=int,
                    default=100)

parser.add_argument('--num-hosts',
                    type=int,
                    help="Number of hosts in th system",
                    default=4)

args = parser.parse_args()

def parse_pcc_log(logfilename):
    tps = []
    with open(logfilename) as f:
        lines = f.readlines()
        for line in lines[1:]:
            tpstr = line.split()[0]
            tps.append(float(tpstr))
    return tps

def parse_iperf_log(logfilename):
    tps = []
    with open(logfilename) as f:
        lines = f.readlines()
        for line in lines[6:6 + args.flow_time]:
            tpstr = line.split()[6]
            if not tpstr[0].isdigit():
                tpstr = line.split()[7]
            tps.append(float(tpstr)) 
    return tps 

def calculate_tcp_fairness():
    offset = args.offset
    fnames = [args.dir + '/monitor_' + str(i)+'.log' for i in range(args.num_hosts)]
    tp = []
    for i, name in enumerate(fnames):
        tp.append(parse_iperf_log(name))
 
    jains = []
    for i in range(args.num_hosts):
        jains.append([])
    
    for i in range((args.num_hosts - 1) * args.offset + args.flow_time):
        flows_on = []
        for j in range(args.num_hosts):
            if i >= j * offset and i < args.flow_time + j * offset:
                flows_on.append(j)
  
              
        if i % 100 == 0:
            avg_flows = [0 for x in range(args.num_hosts)]

        for j in flows_on:
            if i - j*offset < len(tp[j]):
                avg_flows[j] += tp[j][i - j*offset]
        

        if i % 100 == 99:
            jain_num = 0
            jain_denom = 0
            for j in flows_on:
                jain_num += avg_flows[j] / 100
                jain_denom += (avg_flows[j] / 100) * (avg_flows[j] / 100)
            jain_num = jain_num * jain_num;
            jain_denom = len(flows_on) * jain_denom
        
            jains[len(flows_on) -1 ].append(jain_num/jain_denom);


    for i in range(args.num_hosts):
        print("With the number of flows at "+ str(i + 1) +
              ", the Jain fairness for TCP over 100 seconds is " + str( sum(jains[i])/len(jains[i]))) 

    print 


def calculate_pcc_fairness():
    offset = args.offset
    fnames = [args.dir + '/pcc_monitor_' + str(i)+'.log' for i in range(args.num_hosts)]
    tp = []
    for i, name in enumerate(fnames):
        tp.append(parse_pcc_log(name))

    jains = []
    for i in range(args.num_hosts):
        jains.append([])

    for i in range((args.num_hosts - 1) * args.offset + args.flow_time):
        flows_on = []
        for j in range(args.num_hosts):
            if i >= j * offset and i < args.flow_time + j * offset:
                flows_on.append(j)
  
              
        if i % 100 == 0:
            avg_flows = [0 for x in range(args.num_hosts)]

        # Missing the last measurements due to early shutdown
        for j in flows_on:
            if i - j*offset < len(tp[j]):
                avg_flows[j] += tp[j][i - j*offset]

        if i % 100 == 99:
            jain_num = 0
            jain_denom = 0
            for j in flows_on:
                jain_num += avg_flows[j] / 100
                jain_denom += (avg_flows[j] / 100) * (avg_flows[j] / 100)
            jain_num = jain_num * jain_num;
            
            jain_denom = (len(flows_on)) * jain_denom

            jains[len(flows_on) -1 ].append(jain_num/jain_denom);

    for i in range(args.num_hosts):
        print("With the number of flows at "+ str(i + 1) +
              ", the Jain fairness for PCC over 100 seconds is " + str( sum(jains[i])/len(jains[i]))) 

    print

def calculate_TCP_stddev():

    offset = args.offset
    fnames = [args.dir + '/monitor_' + str(i)+'.log' for i in range(args.num_hosts)]
    tp = []
    for i, name in enumerate(fnames):
        tp.append(parse_iperf_log(name))

    std_devs = []
    for i in range(args.num_hosts):
        std_devs.append([])
    
    for i in range(args.num_hosts):
        for j in range(args.num_hosts):
            one_section = tp[j][i * offset: (i+1) * offset]
            index =  abs(abs(args.num_hosts - 1 - (i + j)) - (args.num_hosts - 1))
           
            std_devs[index].append(np.std(one_section))     


    for i in range(args.num_hosts):
        print("The average standard deviation of a TCP flow in a network with "+ str(i + 1) +
              " TCP flows is " + str(sum(std_devs[i])/len(std_devs[i]))) 
    print

def calculate_PCC_stddev():

    offset = args.offset
    fnames = [args.dir + '/pcc_monitor_' + str(i)+'.log' for i in range(args.num_hosts)]
    tp = []
    for i, name in enumerate(fnames):
        tp.append(parse_pcc_log(name))

    std_devs = []
    for i in range(args.num_hosts):
        std_devs.append([])
    
    for i in range(args.num_hosts):
        for j in range(args.num_hosts):
            if i != args.num_hosts - 1:
                one_section = tp[j][i * offset: (i+1) * offset]
            else:
                one_section = tp[j][i * offset:]
            index =  abs(abs(args.num_hosts - 1 - (i + j)) - (args.num_hosts - 1))
           
            std_devs[index].append(np.std(one_section))     


    for i in range(args.num_hosts):
        print("The average standard deviation of a PCC flow in a network with "+ str(i + 1) +
              " PCC flows is " + str(sum(std_devs[i])/len(std_devs[i])))
 
calculate_tcp_fairness()        
calculate_pcc_fairness()
calculate_TCP_stddev()
calculate_PCC_stddev()
