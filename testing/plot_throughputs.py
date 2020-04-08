import os
from helper import *

rootdir = 'output'

def plot_pcc_throughputs(ax):
    pcc_queue_sizes = []
    pcc_throughputs = []

    for i in os.listdir(rootdir + '/PCC'):
        if i.endswith(".log"):
            f = open(rootdir + '/PCC/' + i, 'r')
            throughputs = []
            for line in f:
                gather_pcc_info(throughputs, line)
            f.close() 

            avg = sum(throughputs)/len(throughputs) 
            pcc_throughputs.append(avg)
            file_names = i.split('.')
            pcc_queue_sizes.append(int(file_names[0]) * 1.5)
            

    together = sorted(zip(pcc_queue_sizes, pcc_throughputs))
    qsize_sort = zip(*together)[0]
    tput_sort = zip(*together)[1]
           

    ax.plot(qsize_sort, tput_sort, label='PCC')

def gather_pcc_info(mylist, line):
    data = line.split('\t')
    if data[0][0] != 'S': 
        mylist.append(float(data[0]))


def plot_tcp_throughputs(ax):
    tcp_queue_sizes = []
    tcp_throughputs = []

    
    for i in os.listdir(rootdir + '/TCP'):
        if i.endswith(".log"):
            f = open(rootdir + '/TCP/' + i, 'r')
            
            throughput = gather_tcp_info(f)
            f.close()
            tcp_throughputs.append(throughput)
            file_names = i.split('.')
            tcp_queue_sizes.append(int(file_names[0]) * 1.5 )

    together = sorted(zip(tcp_queue_sizes, tcp_throughputs))
    qsize_sort = zip(*together)[0]
    tput_sort = zip(*together)[1]
           

    ax.plot(qsize_sort, tput_sort, label='TCP Cubic')


def gather_tcp_info(f):
    f.readline()
    f.readline()
    f.readline()
    f.readline()
    f.readline()
    f.readline()
    necessary_line = f.readline()

    return float(necessary_line[34:39])
    

m.rc('figure', figsize=(16, 6))

fig = plt.figure(figsize=[8, 6])
plots = 1

axPlot = fig.add_subplot(1, plots, 1)
plot_pcc_throughputs(axPlot)
plot_tcp_throughputs(axPlot)
plt.legend(loc='lower right')
axPlot.set_xlabel("Queue size (KB)")
axPlot.set_ylabel("Throughput (Mbps)")

plt.title('Mininet Queue Size Sweep')
plt.savefig("Shallow_Queue.png")
