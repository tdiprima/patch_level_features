#!/bin/bash

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
