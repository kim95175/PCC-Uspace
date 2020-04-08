sudo apt-get install g++
sudo apt-get install python-matplotlib
git clone https://github.com/modong/pcc.git
cd ..
git clone git://github.com/mininet/mininet
cd mininet
git checkout 2.2.1
cd ..
mininet/util/install.sh -a
cd cs244_researchpcc
