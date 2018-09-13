import matplotlib.pyplot as plt
plt.switch_backend('agg')
import numpy as np
import collections
import sys
import os
import json 
import datetime
from pymongo import MongoClient


if __name__ == '__main__':
  if len(sys.argv)<0:
    print "usage:python create_patch_level_histogram.py";
    exit();    
  
  #my_home="/data1/bwang"  
  my_home="/home/bwang/patch_level";
  
  picture_folder = os.path.join(my_home, 'patch_level_plot'); 
  if not os.path.exists(picture_folder):
    print '%s folder do not exist, then create it.' % picture_folder;
    os.makedirs(picture_folder);
  
  print " --- read config.json file ---" ;
  config_json_file_name = "config_cluster.json";  
  config_json_file = os.path.join(my_home, config_json_file_name);
  with open(config_json_file) as json_data:
    d = json.load(json_data);     
    patch_size =  d['patch_size'];   
    db_host = d['db_host'];
    db_port = d['db_port'];
    db_name1 = d['db_name1']; 
    db_name2 = d['db_name2'];
    print patch_size,db_host,db_port,db_name1,db_name2;   
      
  client = MongoClient('mongodb://'+db_host+':'+db_port+'/');     
  db = client[db_name1];    
  images =db.images; 
  metadata=db.metadata;
  objects = db.objects;     
  
  db2 = client[db_name2];    
  images2 =db2.images; 
  metadata2=db2.metadata;
  objects2 = db2.objects;  
  
  patch_level_dataset = db2.patch_level_features;  
  patch_level_histogram = db2.features_histogram;
  
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
   
  feature_array=['percent_nuclear_material','nucleus_area','grayscale_segment_mean','grayscale_segment_std','Hematoxylin_segment_mean','Hematoxylin_segment_std','grayscale_patch_mean','grayscale_patch_std','Hematoxylin_patch_mean','Hematoxylin_patch_std','Flatness_segment_mean','Flatness_segment_std','Perimeter_segment_mean','Perimeter_segment_std','Circularity_segment_mean','Circularity_segment_std','r_GradientMean_segment_mean','r_GradientMean_segment_std','b_GradientMean_segment_mean','b_GradientMean_segment_std','r_cytoIntensityMean_segment_mean','r_cytoIntensityMean_segment_std','b_cytoIntensityMean_segment_mean','b_cytoIntensityMean_segment_std','Elongation_segment_mean','Elongation_segment_std']; 
  name_array=['nuclear material percentage (%)','nucleus area (micron square)','grayscale intensity mean','grayscale intensity std','Hematoxylin intensity mean','Hematoxylin intensity std','grayscale_patch_mean','grayscale_patch_std','Hematoxylin_patch_mean','Hematoxylin_patch_std','Flatness_segment_mean','Flatness_segment_std','Perimeter_segment_mean','Perimeter_segment_std','Circularity_segment_mean','Circularity_segment_std','r_GradientMean_segment_mean','r_GradientMean_segment_std','b_GradientMean_segment_mean','b_GradientMean_segment_std','r_cytoIntensityMean_segment_mean','r_cytoIntensityMean_segment_std','b_cytoIntensityMean_segment_mean','b_cytoIntensityMean_segment_std','Elongation_segment_mean','Elongation_segment_std'];    

  data_range="patch_level";
  for case_id in image_array:
    for index,feature in enumerate(feature_array):         
      feature_value_array=[];   
      hist_count_array=[];
      bin_edges_array=[];
          
      for record in patch_level_dataset.find({"case_id":case_id,"tumorFlag" : "tumor","$and":[{feature:{ "$ne": "n/a" }},{feature:{ "$gte": 0.0 }}]} ,{feature:1,"_id":0}):
        feature_value=record[feature];
        feature_value_array.append(feature_value); 
      print case_id,feature;   
      #print feature_value_array; 
      total_patch_count=len(feature_value_array); 
      if len(feature_value_array) >0: 
        fig, ax = plt.subplots();    
        n, bins, patches = plt.hist(feature_value_array, bins='auto',facecolor='blue');      
        plt.xlabel(name_array[index])
        plt.ylabel('Patch Count')
        plt.title("patch level "+ feature+ ' Histogram of image '+ str(case_id))
        #Tweak spacing to prevent clipping of ylabel
        plt.subplots_adjust(left=0.15)
        plt.grid(True);           
        # place a text box in upper left in axes coords
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        textstr="Total patch count: " + str(total_patch_count);
        ax.text(0.6, 0.95, textstr, transform=ax.transAxes, fontsize=10, verticalalignment='top', bbox=props);      
        #plt.show();
        file_name="patch_level_histogram_"+case_id+"_"+feature+".png";  
        graphic_file_path = os.path.join(picture_folder, file_name);
        plt.savefig(graphic_file_path); 
        plt.gcf().clear();       
  exit(); 

