
How to use cluster to generate patch level features data:

1) files involved: run_jobs.sh,run_jobs.pbs,run_jobs.py,config_cluster.json,
                   image_user_list.txt,image_path.txt,generate_heatmap.py,config.json
                   
2a) copy config_cluster.json and image_path.txt to 10 cluster node
2b) copy  case_id_prefix.txt to 10 computing node;
    pdsh -w node[001-010] cp -rf /home/bwang/patch_level/case_id_prefix.txt  /data1/bwang/case_id_prefix.txt 

3a) command: sh run_jobs.sh
            enter image user list file:
            image_user_list.txt
            
3b) files involved run_jobs.sh,run_jobs.pbs,run_jobs.py,config_cluster.json,
                   image_user_list.txt,image_path.txt,case_id_prefix.txt;
                   
4)log file location: cluster /home/bwang/temp/logs/pbs/    

5) features dataset has been saved to quip3 mongo db "quip_comp" collection "patch_level_dataset";

6a) run generate_heatmap.py to generate and load heatmap to quip db in quip3 server;

6b) files involved generate_heatmap.py,config.json,image_user_list.txt
