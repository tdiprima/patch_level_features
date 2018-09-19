#!/usr/bin/env bash

#!/bin/bash

echo "-----------------------------------------------------"
echo "Date: $(date)                      Host: $(hostname) "
echo "-----------------------------------------------------"
echo "BEGIN"

python myscript.py -s PC_051_0_1 -u dr.rajarsi.gupta -b quip3.bmi.stonybrook.edu -p 512

echo "END"
echo "Date: $(date)"