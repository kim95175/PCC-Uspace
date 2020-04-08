Running Our Experiment
Evan Cheshire && Wyatt Daviau
2016 CS 244 Experiments to Reproduce PCC performance and fairness assessment

***********************************************
* Using our Provided Amazon AMI (Recommended) *
***********************************************

We have provided an Amazon AMI which you can use to launch an EC2 instance with our
 code already installed and ready to run.  To get setup begin by going to your AWS 
EC2 management console and click "Launch Instance." Make sure that your region is
set to "Oregon" using the region tab at the top right of your screen.  In the gray 
box on the left of the screen click on the "Community AMIs" tab.  Next copy our AMI
code 21e21b41 into the "Search community AMIs" box.  Select this AMI and choose 
the c4-2XL instance type to launch the instance.

To login to the instance return to your EC2 management console and wait for the 
instance to finish initializing.  Use the public DNS of the form 
ec2-xx-yy-zzz-aaa.us-west-2.compute.amazonaws.com to ssh into the instance as user
"ubuntu".  Assuming you've kept track of your key in key.pem your command will look
like: ssh -i key.pem ubuntu@ec2-xx-yy-zzz-aaa.us-west-2.compute.amazonaws.com.

Once you have gained access type the sequence of commands below to run experiments 
and plot our data.  Note that our experiments take about 3 hours total to run 
(1 hour PCC multiflow, 1 hour TCP multiflow, 1 hour Shallow-Queue Sweep), so please
be patient.  We've included mininet cleanup calls in between runs to ensure smooth 
sailing.  The commands:

cd cs244_researchpcc
sudo ./shallow-queue.sh
sudo mn -c
sudo ./multi-flow.sh

This will run both experiments, generating the TCP and PCC 4 flow convergence tests
and queue sweeps.  The output plots of interest are pccmulti.png, tcpmulti.png, and
Shallow_Queue.png.  These plots will be saved in your current directory and can be 
sent back to your host for viewing using scp.

If you are interested in recreating our PCC 2-flow convergence test feel free to
modify multi-flow.sh to have 4 hosts with a flow_time of 1000 each and then rerun. 
However this plot was mainly included for a clear visual comparison with the Emulab
results.  It is a subset of the 4 flow convergence test and therefore need not be 
reproduced for 244 purposes.  Similarly we included a convergence test on a machine
with fewer cores to highlight our experimental process but it is not the core 
result we are presenting.  However, if you are interested in reproducing the plots 
of the convergence test on fewer cores you simply need to run the AMI in an 
m4-large instance and repeat the process above. 

Mo Dong graciously helped us get access to Emulab, however he cannot extend the 
same courtesy to everyone.  If you want to reproduce the Emulab section of the 
results you can contact the Emulab admins and can apply for time based on their 
rules [2]. 

*************************
* Starting from Scratch *
*************************

If you would like to run these experiments without the machine image we have a 
public git repository that can be used to setup a new instance from scratch. 
Launch and login to a new c4-2XL ubuntu instance and launch the following commands:

sudo apt-get update
sudo apt-get install git
git clone https://bitbucket.org/ZenGround0/cs244_researchpcc.git
cd cs244_researchpcc
sudo ./start_me_up.sh

At this point mininet [3] and the PCC source [4] are installed along with 
matplotlib.  To make PCC with the utility function in the paper edit 
pcc/sender/app/cc.h by commenting out line 303 and uncommenting line 302. Next 
return to cs244_researchpcc and run our simple install script to make pcc:

sudo ./install_pcc.sh

At this point your instance should be in the same state as our AMI.  See the above 
section for running the experiments and generating plots.
