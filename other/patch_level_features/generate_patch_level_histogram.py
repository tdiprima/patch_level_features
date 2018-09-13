import matplotlib.pyplot as plt
import numpy as np
import collections
import sys
import os
import json 
import datetime
from pymongo import MongoClient


if __name__ == '__main__':
  if len(sys.argv)<1:
    print "usage:python generate_patch_level_histogram.py config.json";
    exit();  
  
  local_folder="/home/bwang/patch_level";
  picture_folder = os.path.join(local_folder, 'picture'); 
  
  print " --- read config.json file ---" ;
  config_json_file = sys.argv[-1];  
  with open(config_json_file) as json_data:
    d = json.load(json_data);        
    patch_size =  d['patch_size'];   
    db_host = d['db_host'];
    db_port = d['db_port'];
    db_name1 = d['db_name1']; 
    db_name2 = d['db_name2'];
    print patch_size,db_host,db_port,db_name1,db_name2;
  #exit();   
      
  client = MongoClient('mongodb://'+db_host+':'+db_port+'/');     
  db = client[db_name1];    
  images =db.images; 
  metadata=db.metadata;
  objects = db.objects;     
  
  db2 = client[db_name2];    
  images2 =db2.images; 
  metadata2=db2.metadata;
  objects2 = db2.objects;    
  
  patch_level_dataset = db2.patch_level_features_run2;  
  patch_level_histogram = db2.patch_level_histogram;
  
  #########################################
  def saveHistogram(case_id,feature,data_range,hist_count_array,bin_edges_array):
    dict_patch = collections.OrderedDict();
    dict_patch['case_id'] = case_id
    dict_patch['feature'] = feature
    dict_patch['data_range'] = data_range    
    dict_patch['hist_count_array'] = hist_count_array
    dict_patch['bin_edges_array'] = bin_edges_array    
    dict_patch['date'] = datetime.datetime.now();    
    patch_level_histogram.insert_one(dict_patch);   
  #########################################
  
  image_array=[];  
  for record in patch_level_dataset.distinct("case_id"):    
    image_array.append(record); 
    
  feature_array=['nucleus_area','percent_nuclear_material','grayscale_segment_mean','grayscale_segment_std','Hematoxylin_segment_mean','Hematoxylin_segment_std','grayscale_patch_mean','grayscale_patch_std','Hematoxylin_patch_mean','Hematoxylin_patch_std','Flatness_segment_mean','Flatness_segment_std','Perimeter_segment_mean','Perimeter_segment_std','Circularity_segment_mean','Circularity_segment_std','r_GradientMean_segment_mean','r_GradientMean_segment_std','b_GradientMean_segment_mean','b_GradientMean_segment_std','r_cytoIntensityMean_segment_mean','r_cytoIntensityMean_segment_std','b_cytoIntensityMean_segment_mean','b_cytoIntensityMean_segment_std','Elongation_segment_mean','Elongation_segment_std']; 
   
  data_range="patch level";
  for case_id in image_array:    
    for feature in feature_array:         
      feature_value_array=[];   
      hist_count_array=[];
      bin_edges_array=[];
      
      for record in patch_level_dataset.find({"case_id":case_id,"$and":[{feature:{ "$ne": "n/a" }},{feature:{ "$gte": 0.0 }}]} ,{feature:1,"_id":0}):
        feature_value=record[feature];
        feature_value_array.append(feature_value); 
      print case_id,feature;   
      #print feature_value_array;  
            
      n, bins, patches = plt.hist(feature_value_array,  bins='auto',facecolor='#0504aa',alpha=0.5)      
      plt.xlabel(feature)
      plt.ylabel('Patch Count')
      plt.title("patch level "+ feature+ ' Histogram of image '+ str(case_id))
      #Tweak spacing to prevent clipping of ylabel
      plt.subplots_adjust(left=0.15)
      plt.grid(True);
      plt.show();
      file_name="patch_level_histogram_"+case_id+"_"+feature+".png";  
      graphic_file_path = os.path.join(picture_folder, file_name);
      plt.savefig(graphic_file_path);                
      for count in n:        
        hist_count_array.append(int(count));
      for bin_edge in bins:        
        bin_edges_array.append(float(bin_edge)); 
      saveHistogram(case_id,feature,data_range,hist_count_array,bin_edges_array);  
  exit(); 

