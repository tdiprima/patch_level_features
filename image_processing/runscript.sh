#!/usr/bin/env bash
# This script prints the current date and host details, activates a virtual environment, executes a python script
# (myscript.py) with specified arguments, and prints 'END' along with the current date.

echo "-----------------------------------------------------"
echo "Date: $(date)                      Host: $(hostname) "
echo "-----------------------------------------------------"
echo "BEGIN"

source activate myenv
python myscript.py -s [slide] -u [user] -b [db] -p 512

echo "END"
echo "Date: $(date)"
