#!/bin/bash
# Reads a specified file (or 'image_user_list.txt' by default) line by line, splits each line into an array using comma
# as a separator, assigns variable values from the array elements to 'case_id', 'user', and 'size', then submits a job
# (myscript.pbs) to a PBS queue with the 'case_id' and 'user' as environment variables.

if [ -z "$1" ]
  then
    filename="image_user_list.txt"
else
    filename="$1"
fi

while IFS='' read -r line || [[ -n "$line" ]];
do  
  IFS=', ' read -r -a array <<< "$line"  
  case_id="${array[0]}"
  user="${array[1]}"
  size="${array[2]}"
  qsub -v caseid=$case_id,user=$user myscript.pbs  
done < $filename
