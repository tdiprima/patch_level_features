#!/usr/bin/env bash

echo "-----------------------------------------------------"
echo "Date: $(date)                      Host: $(hostname) "
echo "-----------------------------------------------------"
echo "BEGIN"

source activate myenv
python myscript.py -s [slide] -u [user] -b [db] -p 512

echo "END"
echo "Date: $(date)"
