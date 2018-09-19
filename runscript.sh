#!/usr/bin/env bash

#!/bin/bash

echo "-----------------------------------------------------"
echo "Date: $(date)                      Host: $(hostname) "
echo "-----------------------------------------------------"
echo "BEGIN"

python myscript.py -s [slide] -u [user] -b [db] -p 512

echo "END"
echo "Date: $(date)"