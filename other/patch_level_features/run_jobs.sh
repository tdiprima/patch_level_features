#!/bin/bash

echo "Please enter image_user_list filename:"
read filename
while IFS='' read -r line || [[ -n "$line" ]]; 
do  
  IFS=', ' read -r -a array <<< "$line"  
  case_id="${array[0]}"
  user="${array[1]}"
  #echo $case_id, $user
  qsub -v caseid=$case_id,user=$user run_jobs.pbs  
done < $filename
