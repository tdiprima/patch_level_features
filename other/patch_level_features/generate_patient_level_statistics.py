from shapely.geometry import LineString
from shapely.geometry.polygon import LinearRing
from shapely.geometry import Polygon
from shapely.geometry import MultiPolygon
from shapely.affinity import affine_transform
from shapely import ops
from skimage import color
from skimage import io
from skimage.color import separate_stains,hed_from_rgb
from skimage import data
from pymongo import MongoClient
from bson import json_util 
from matplotlib.path import Path
from PIL import Image
import openslide
import numpy as np
import time
import pprint
import json 
import collections
import csv
import sys
import os
import shutil
import subprocess
import pipes
import shlex
import math
import datetime
import random

    
    
if __name__ == '__main__':
  if len(sys.argv)<1:
    print "usage:python generate_patient_level_statistics.py config.json";
    exit(); 
   
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
  
  patch_level_dataset = db2.patch_level_features;
  collection_saved    = db2.patient_level_statistics;  
  
  region_type="tumor";
  #region_type="non_tumor"; 
  
  image_list=[]; 
  print '--- process image_list  ---- ';   
  for case_id in patch_level_dataset.distinct("case_id"):    
    image_list.append(case_id);
  print image_list;  
  #exit();
  
  for case_id in image_list:  
    print   case_id;      
    percent_nuclear_material_array=[];
    grayscale_patch_mean_array=[];
    grayscale_patch_std_array=[];
    Hematoxylin_patch_mean_array=[];
    Hematoxylin_patch_std_array=[];     
    Flatness_segment_mean_array=[]; 
    Flatness_segment_std_array=[];
    Perimeter_segment_mean_array=[];
    Perimeter_segment_std_array=[];
    Circularity_segment_mean_array=[];
    Circularity_segment_std_array=[];
    r_GradientMean_segment_mean_array=[];
    r_GradientMean_segment_std_array=[];
    b_GradientMean_segment_mean_array=[];
    b_GradientMean_segment_std_array=[];
    r_cytoIntensityMean_segment_mean_array=[];
    r_cytoIntensityMean_segment_std_array=[];
    b_cytoIntensityMean_segment_mean_array=[];
    b_cytoIntensityMean_segment_std_array=[];    
     
    #for feature_record in patch_level_dataset.find({"case_id":case_id,                                                    
                                                    #"tumorFlag":region_type,
                                                    #"percent_nuclear_material": { "$gte": 2.0 }}):
                                                    
    for feature_record in patch_level_dataset.find({"case_id":case_id,                                                    
                                                    "tumorFlag":region_type,
                                                    "$and":[{ "percent_nuclear_material":{ "$gte": 2.0 } },{ "percent_nuclear_material":{ "$lte": 90.0 }}]}):  
                                                    
      percent_nuclear_material=feature_record["percent_nuclear_material"];
      grayscale_patch_mean=feature_record["grayscale_patch_mean"];
      grayscale_patch_std=feature_record["grayscale_patch_std"];
      Hematoxylin_patch_mean=feature_record["Hematoxylin_patch_mean"];
      Hematoxylin_patch_std=feature_record["Hematoxylin_patch_std"];      
      Flatness_segment_mean=feature_record["Flatness_segment_mean"];
      Flatness_segment_std=feature_record["Flatness_segment_std"];
      Perimeter_segment_mean=feature_record["Perimeter_segment_mean"];
      Perimeter_segment_std=feature_record["Perimeter_segment_std"];      
      Circularity_segment_mean=feature_record["Circularity_segment_mean"];
      Circularity_segment_std=feature_record["Circularity_segment_std"];
      r_GradientMean_segment_mean=feature_record["r_GradientMean_segment_mean"];
      r_GradientMean_segment_std=feature_record["r_GradientMean_segment_std"];
      b_GradientMean_segment_mean=feature_record["b_GradientMean_segment_mean"];
      b_GradientMean_segment_std=feature_record["b_GradientMean_segment_std"];
      r_cytoIntensityMean_segment_mean=feature_record["r_cytoIntensityMean_segment_mean"];
      r_cytoIntensityMean_segment_std=feature_record["r_cytoIntensityMean_segment_std"];
      b_cytoIntensityMean_segment_mean=feature_record["b_cytoIntensityMean_segment_mean"];
      b_cytoIntensityMean_segment_std=feature_record["b_cytoIntensityMean_segment_std"];   
        
      percent_nuclear_material_array.append(percent_nuclear_material);         
      grayscale_patch_mean_array.append(grayscale_patch_mean);
      grayscale_patch_std_array.append(grayscale_patch_std);
      Hematoxylin_patch_mean_array.append(Hematoxylin_patch_mean);
      Hematoxylin_patch_std_array.append(Hematoxylin_patch_std);
      Flatness_segment_mean_array.append(Flatness_segment_mean); 
      Flatness_segment_std_array.append(Flatness_segment_std);
      Perimeter_segment_mean_array.append(Perimeter_segment_mean);
      Perimeter_segment_std_array.append(Perimeter_segment_std);
      Circularity_segment_mean_array.append(Circularity_segment_mean);
      Circularity_segment_std_array.append(Circularity_segment_std);
      r_GradientMean_segment_mean_array.append(r_GradientMean_segment_mean);
      r_GradientMean_segment_std_array.append(r_GradientMean_segment_std);
      b_GradientMean_segment_mean_array.append(b_GradientMean_segment_mean);
      b_GradientMean_segment_std_array.append(b_GradientMean_segment_std);
      r_cytoIntensityMean_segment_mean_array.append(r_cytoIntensityMean_segment_mean);
      r_cytoIntensityMean_segment_std_array.append(r_cytoIntensityMean_segment_std);
      b_cytoIntensityMean_segment_mean_array.append(b_cytoIntensityMean_segment_mean);
      b_cytoIntensityMean_segment_std_array.append(b_cytoIntensityMean_segment_std);      
      
      
    dict_data = collections.OrderedDict(); 
    dict_data['case_id']=case_id;
    dict_data['datetime'] = datetime.datetime.now();
    
    #calculate percentile value
    percent_nuclear_material_10th_percentile=np.percentile(percent_nuclear_material_array,10);
    percent_nuclear_material_25th_percentile=np.percentile(percent_nuclear_material_array,25);
    percent_nuclear_material_50th_percentile=np.percentile(percent_nuclear_material_array,50);
    percent_nuclear_material_75th_percentile=np.percentile(percent_nuclear_material_array,75);
    percent_nuclear_material_90th_percentile=np.percentile(percent_nuclear_material_array,90);    
    dict_percent_nuclear_material = {}
    dict_percent_nuclear_material['10th'] = percent_nuclear_material_10th_percentile;
    dict_percent_nuclear_material['25th'] = percent_nuclear_material_25th_percentile;
    dict_percent_nuclear_material['50th'] = percent_nuclear_material_50th_percentile; 
    dict_percent_nuclear_material['75th'] = percent_nuclear_material_75th_percentile;
    dict_percent_nuclear_material['90th'] = percent_nuclear_material_90th_percentile;   
    dict_data['percent_nuclear_material'] = dict_percent_nuclear_material;
    
    grayscale_patch_mean_10th_percentile=np.percentile(grayscale_patch_mean_array,10);
    grayscale_patch_mean_25th_percentile=np.percentile(grayscale_patch_mean_array,25);
    grayscale_patch_mean_50th_percentile=np.percentile(grayscale_patch_mean_array,50);
    grayscale_patch_mean_75th_percentile=np.percentile(grayscale_patch_mean_array,75);
    grayscale_patch_mean_90th_percentile=np.percentile(grayscale_patch_mean_array,90); 
    dict_grayscale_patch_mean = {}
    dict_grayscale_patch_mean['10th'] = grayscale_patch_mean_10th_percentile;
    dict_grayscale_patch_mean['25th'] = grayscale_patch_mean_25th_percentile;
    dict_grayscale_patch_mean['50th'] = grayscale_patch_mean_50th_percentile; 
    dict_grayscale_patch_mean['75th'] = grayscale_patch_mean_75th_percentile;
    dict_grayscale_patch_mean['90th'] = grayscale_patch_mean_90th_percentile;   
    dict_data['grayscale_patch_mean'] = dict_grayscale_patch_mean;
    
    grayscale_patch_std_10th_percentile=np.percentile(grayscale_patch_std_array,10);
    grayscale_patch_std_25th_percentile=np.percentile(grayscale_patch_std_array,25);
    grayscale_patch_std_50th_percentile=np.percentile(grayscale_patch_std_array,50);
    grayscale_patch_std_75th_percentile=np.percentile(grayscale_patch_std_array,75);
    grayscale_patch_std_90th_percentile=np.percentile(grayscale_patch_std_array,90); 
    dict_grayscale_patch_std = {}
    dict_grayscale_patch_std['10th'] = grayscale_patch_std_10th_percentile;
    dict_grayscale_patch_std['25th'] = grayscale_patch_std_25th_percentile;
    dict_grayscale_patch_std['50th'] = grayscale_patch_std_50th_percentile; 
    dict_grayscale_patch_std['75th'] = grayscale_patch_std_75th_percentile;
    dict_grayscale_patch_std['90th'] = grayscale_patch_std_90th_percentile;   
    dict_data['grayscale_patch_std'] = dict_grayscale_patch_std;
    
    Hematoxylin_patch_mean_10th_percentile=np.percentile(Hematoxylin_patch_mean_array,10);
    Hematoxylin_patch_mean_25th_percentile=np.percentile(Hematoxylin_patch_mean_array,25);
    Hematoxylin_patch_mean_50th_percentile=np.percentile(Hematoxylin_patch_mean_array,50);
    Hematoxylin_patch_mean_75th_percentile=np.percentile(Hematoxylin_patch_mean_array,75);
    Hematoxylin_patch_mean_90th_percentile=np.percentile(Hematoxylin_patch_mean_array,90); 
    dict_Hematoxylin_patch_mean = {}
    dict_Hematoxylin_patch_mean['10th'] = Hematoxylin_patch_mean_10th_percentile;
    dict_Hematoxylin_patch_mean['25th'] = Hematoxylin_patch_mean_25th_percentile;
    dict_Hematoxylin_patch_mean['50th'] = Hematoxylin_patch_mean_50th_percentile; 
    dict_Hematoxylin_patch_mean['75th'] = Hematoxylin_patch_mean_75th_percentile;
    dict_Hematoxylin_patch_mean['90th'] = Hematoxylin_patch_mean_90th_percentile;   
    dict_data['Hematoxylin_patch_mean'] = dict_Hematoxylin_patch_mean;    
    
    Hematoxylin_patch_std_10th_percentile=np.percentile(Hematoxylin_patch_std_array,10);
    Hematoxylin_patch_std_25th_percentile=np.percentile(Hematoxylin_patch_std_array,25);
    Hematoxylin_patch_std_50th_percentile=np.percentile(Hematoxylin_patch_std_array,50);
    Hematoxylin_patch_std_75th_percentile=np.percentile(Hematoxylin_patch_std_array,75);
    Hematoxylin_patch_std_90th_percentile=np.percentile(Hematoxylin_patch_std_array,90); 
    dict_Hematoxylin_patch_std = {}
    dict_Hematoxylin_patch_std['10th'] = Hematoxylin_patch_std_10th_percentile;
    dict_Hematoxylin_patch_std['25th'] = Hematoxylin_patch_std_25th_percentile;
    dict_Hematoxylin_patch_std['50th'] = Hematoxylin_patch_std_50th_percentile; 
    dict_Hematoxylin_patch_std['75th'] = Hematoxylin_patch_std_75th_percentile;
    dict_Hematoxylin_patch_std['90th'] = Hematoxylin_patch_std_90th_percentile;   
    dict_data['Hematoxylin_patch_std'] = dict_Hematoxylin_patch_std;    
    
    Flatness_segment_mean_10th_percentile=np.percentile(Flatness_segment_mean_array,10);
    Flatness_segment_mean_25th_percentile=np.percentile(Flatness_segment_mean_array,25);
    Flatness_segment_mean_50th_percentile=np.percentile(Flatness_segment_mean_array,50);
    Flatness_segment_mean_75th_percentile=np.percentile(Flatness_segment_mean_array,75);
    Flatness_segment_mean_90th_percentile=np.percentile(Flatness_segment_mean_array,90);   
    dict_Flatness_segment_mean = {}
    dict_Flatness_segment_mean['10th'] = Flatness_segment_mean_10th_percentile;
    dict_Flatness_segment_mean['25th'] = Flatness_segment_mean_25th_percentile;
    dict_Flatness_segment_mean['50th'] = Flatness_segment_mean_50th_percentile; 
    dict_Flatness_segment_mean['75th'] = Flatness_segment_mean_75th_percentile;
    dict_Flatness_segment_mean['90th'] = Flatness_segment_mean_90th_percentile;   
    dict_data['Flatness_segment_mean'] = dict_Flatness_segment_mean;      
    
    Flatness_segment_std_10th_percentile=np.percentile(Flatness_segment_std_array,10);
    Flatness_segment_std_25th_percentile=np.percentile(Flatness_segment_std_array,25);
    Flatness_segment_std_50th_percentile=np.percentile(Flatness_segment_std_array,50);
    Flatness_segment_std_75th_percentile=np.percentile(Flatness_segment_std_array,75);
    Flatness_segment_std_90th_percentile=np.percentile(Flatness_segment_std_array,90);
    dict_Flatness_segment_std = {}
    dict_Flatness_segment_std['10th'] = Flatness_segment_std_10th_percentile;
    dict_Flatness_segment_std['25th'] = Flatness_segment_std_25th_percentile;
    dict_Flatness_segment_std['50th'] = Flatness_segment_std_50th_percentile; 
    dict_Flatness_segment_std['75th'] = Flatness_segment_std_75th_percentile;
    dict_Flatness_segment_std['90th'] = Flatness_segment_std_90th_percentile;   
    dict_data['Flatness_segment_std'] = dict_Flatness_segment_std;
    
    
    Perimeter_segment_mean_10th_percentile=np.percentile(Perimeter_segment_mean_array,10);
    Perimeter_segment_mean_25th_percentile=np.percentile(Perimeter_segment_mean_array,25);
    Perimeter_segment_mean_50th_percentile=np.percentile(Perimeter_segment_mean_array,50);
    Perimeter_segment_mean_75th_percentile=np.percentile(Perimeter_segment_mean_array,75);
    Perimeter_segment_mean_90th_percentile=np.percentile(Perimeter_segment_mean_array,90);   
    dict_Perimeter_segment_mean = {}
    dict_Perimeter_segment_mean['10th'] = Perimeter_segment_mean_10th_percentile;
    dict_Perimeter_segment_mean['25th'] = Perimeter_segment_mean_25th_percentile;
    dict_Perimeter_segment_mean['50th'] = Perimeter_segment_mean_50th_percentile; 
    dict_Perimeter_segment_mean['75th'] = Perimeter_segment_mean_75th_percentile;
    dict_Perimeter_segment_mean['90th'] = Perimeter_segment_mean_90th_percentile;   
    dict_data['Perimeter_segment_mean'] = dict_Perimeter_segment_mean;
    
    Perimeter_segment_std_10th_percentile=np.percentile(Perimeter_segment_std_array,10);
    Perimeter_segment_std_25th_percentile=np.percentile(Perimeter_segment_std_array,25);
    Perimeter_segment_std_50th_percentile=np.percentile(Perimeter_segment_std_array,50);
    Perimeter_segment_std_75th_percentile=np.percentile(Perimeter_segment_std_array,75);
    Perimeter_segment_std_90th_percentile=np.percentile(Perimeter_segment_std_array,90);
    dict_Perimeter_segment_std = {}
    dict_Perimeter_segment_std['10th'] = Perimeter_segment_std_10th_percentile;
    dict_Perimeter_segment_std['25th'] = Perimeter_segment_std_25th_percentile;
    dict_Perimeter_segment_std['50th'] = Perimeter_segment_std_50th_percentile; 
    dict_Perimeter_segment_std['75th'] = Perimeter_segment_std_75th_percentile;
    dict_Perimeter_segment_std['90th'] = Perimeter_segment_std_90th_percentile;   
    dict_data['Perimeter_segment_std'] = dict_Perimeter_segment_std;
    
    Circularity_segment_mean_10th_percentile=np.percentile(Circularity_segment_mean_array,10);
    Circularity_segment_mean_25th_percentile=np.percentile(Circularity_segment_mean_array,25);
    Circularity_segment_mean_50th_percentile=np.percentile(Circularity_segment_mean_array,50);
    Circularity_segment_mean_75th_percentile=np.percentile(Circularity_segment_mean_array,75);
    Circularity_segment_mean_90th_percentile=np.percentile(Circularity_segment_mean_array,90);   
    dict_Circularity_segment_mean = {}
    dict_Circularity_segment_mean['10th'] = Circularity_segment_mean_10th_percentile;
    dict_Circularity_segment_mean['25th'] = Circularity_segment_mean_25th_percentile;
    dict_Circularity_segment_mean['50th'] = Circularity_segment_mean_50th_percentile; 
    dict_Circularity_segment_mean['75th'] = Circularity_segment_mean_75th_percentile;
    dict_Circularity_segment_mean['90th'] = Circularity_segment_mean_90th_percentile;   
    dict_data['Circularity_segment_mean'] = dict_Circularity_segment_mean;
    
    Circularity_segment_std_10th_percentile=np.percentile(Circularity_segment_std_array,10);
    Circularity_segment_std_25th_percentile=np.percentile(Circularity_segment_std_array,25);
    Circularity_segment_std_50th_percentile=np.percentile(Circularity_segment_std_array,50);
    Circularity_segment_std_75th_percentile=np.percentile(Circularity_segment_std_array,75);
    Circularity_segment_std_90th_percentile=np.percentile(Circularity_segment_std_array,90);
    dict_Circularity_segment_std = {}
    dict_Circularity_segment_std['10th'] = Circularity_segment_std_10th_percentile;
    dict_Circularity_segment_std['25th'] = Circularity_segment_std_25th_percentile;
    dict_Circularity_segment_std['50th'] = Circularity_segment_std_50th_percentile; 
    dict_Circularity_segment_std['75th'] = Circularity_segment_std_75th_percentile;
    dict_Circularity_segment_std['90th'] = Circularity_segment_std_90th_percentile;   
    dict_data['Circularity_segment_std'] = dict_Circularity_segment_std;  
      
    r_GradientMean_segment_mean_10th_percentile=np.percentile(r_GradientMean_segment_mean_array,10);
    r_GradientMean_segment_mean_25th_percentile=np.percentile(r_GradientMean_segment_mean_array,25);
    r_GradientMean_segment_mean_50th_percentile=np.percentile(r_GradientMean_segment_mean_array,50);
    r_GradientMean_segment_mean_75th_percentile=np.percentile(r_GradientMean_segment_mean_array,75);
    r_GradientMean_segment_mean_90th_percentile=np.percentile(r_GradientMean_segment_mean_array,90);   
    dict_r_GradientMean_segment_mean = {}
    dict_r_GradientMean_segment_mean['10th'] = r_GradientMean_segment_mean_10th_percentile;
    dict_r_GradientMean_segment_mean['25th'] = r_GradientMean_segment_mean_25th_percentile;
    dict_r_GradientMean_segment_mean['50th'] = r_GradientMean_segment_mean_50th_percentile; 
    dict_r_GradientMean_segment_mean['75th'] = r_GradientMean_segment_mean_75th_percentile;
    dict_r_GradientMean_segment_mean['90th'] = r_GradientMean_segment_mean_90th_percentile;   
    dict_data['r_GradientMean_segment_mean'] = dict_r_GradientMean_segment_mean;
    
    r_GradientMean_segment_std_10th_percentile=np.percentile(r_GradientMean_segment_std_array,10);
    r_GradientMean_segment_std_25th_percentile=np.percentile(r_GradientMean_segment_std_array,25);
    r_GradientMean_segment_std_50th_percentile=np.percentile(r_GradientMean_segment_std_array,50);
    r_GradientMean_segment_std_75th_percentile=np.percentile(r_GradientMean_segment_std_array,75);
    r_GradientMean_segment_std_90th_percentile=np.percentile(r_GradientMean_segment_std_array,90);
    dict_r_GradientMean_segment_std = {}
    dict_r_GradientMean_segment_std['10th'] = r_GradientMean_segment_std_10th_percentile;
    dict_r_GradientMean_segment_std['25th'] = r_GradientMean_segment_std_25th_percentile;
    dict_r_GradientMean_segment_std['50th'] = r_GradientMean_segment_std_50th_percentile; 
    dict_r_GradientMean_segment_std['75th'] = r_GradientMean_segment_std_75th_percentile;
    dict_r_GradientMean_segment_std['90th'] = r_GradientMean_segment_std_90th_percentile;   
    dict_data['r_GradientMean_segment_std'] = dict_r_GradientMean_segment_std;    
      
    b_GradientMean_segment_mean_10th_percentile=np.percentile(b_GradientMean_segment_mean_array,10);
    b_GradientMean_segment_mean_25th_percentile=np.percentile(b_GradientMean_segment_mean_array,25);
    b_GradientMean_segment_mean_50th_percentile=np.percentile(b_GradientMean_segment_mean_array,50);
    b_GradientMean_segment_mean_75th_percentile=np.percentile(b_GradientMean_segment_mean_array,75);
    b_GradientMean_segment_mean_90th_percentile=np.percentile(b_GradientMean_segment_mean_array,90);   
    dict_b_GradientMean_segment_mean = {}
    dict_b_GradientMean_segment_mean['10th'] = b_GradientMean_segment_mean_10th_percentile;
    dict_b_GradientMean_segment_mean['25th'] = b_GradientMean_segment_mean_25th_percentile;
    dict_b_GradientMean_segment_mean['50th'] = b_GradientMean_segment_mean_50th_percentile; 
    dict_b_GradientMean_segment_mean['75th'] = b_GradientMean_segment_mean_75th_percentile;
    dict_b_GradientMean_segment_mean['90th'] = b_GradientMean_segment_mean_90th_percentile;   
    dict_data['b_GradientMean_segment_mean'] = dict_b_GradientMean_segment_mean;
    
    b_GradientMean_segment_std_10th_percentile=np.percentile(b_GradientMean_segment_std_array,10);
    b_GradientMean_segment_std_25th_percentile=np.percentile(b_GradientMean_segment_std_array,25);
    b_GradientMean_segment_std_50th_percentile=np.percentile(b_GradientMean_segment_std_array,50);
    b_GradientMean_segment_std_75th_percentile=np.percentile(b_GradientMean_segment_std_array,75);
    b_GradientMean_segment_std_90th_percentile=np.percentile(b_GradientMean_segment_std_array,90);   
    dict_b_GradientMean_segment_std = {}
    dict_b_GradientMean_segment_std['10th'] = b_GradientMean_segment_std_10th_percentile;
    dict_b_GradientMean_segment_std['25th'] = b_GradientMean_segment_std_25th_percentile;
    dict_b_GradientMean_segment_std['50th'] = b_GradientMean_segment_std_50th_percentile; 
    dict_b_GradientMean_segment_std['75th'] = b_GradientMean_segment_std_75th_percentile;
    dict_b_GradientMean_segment_std['90th'] = b_GradientMean_segment_std_90th_percentile;   
    dict_data['b_GradientMean_segment_std'] = dict_b_GradientMean_segment_std; 
       
    r_cytoIntensityMean_segment_mean_10th_percentile=np.percentile(r_cytoIntensityMean_segment_mean_array,10);
    r_cytoIntensityMean_segment_mean_25th_percentile=np.percentile(r_cytoIntensityMean_segment_mean_array,25);
    r_cytoIntensityMean_segment_mean_50th_percentile=np.percentile(r_cytoIntensityMean_segment_mean_array,50);
    r_cytoIntensityMean_segment_mean_75th_percentile=np.percentile(r_cytoIntensityMean_segment_mean_array,75);
    r_cytoIntensityMean_segment_mean_90th_percentile=np.percentile(r_cytoIntensityMean_segment_mean_array,90);   
    dict_r_cytoIntensityMean_segment_mean = {}
    dict_r_cytoIntensityMean_segment_mean['10th'] = r_cytoIntensityMean_segment_mean_10th_percentile;
    dict_r_cytoIntensityMean_segment_mean['25th'] = r_cytoIntensityMean_segment_mean_25th_percentile;
    dict_r_cytoIntensityMean_segment_mean['50th'] = r_cytoIntensityMean_segment_mean_50th_percentile; 
    dict_r_cytoIntensityMean_segment_mean['75th'] = r_cytoIntensityMean_segment_mean_75th_percentile;
    dict_r_cytoIntensityMean_segment_mean['90th'] = r_cytoIntensityMean_segment_mean_90th_percentile;   
    dict_data['r_cytoIntensityMean_segment_mean'] = dict_r_cytoIntensityMean_segment_mean;
    
    r_cytoIntensityMean_segment_std_10th_percentile=np.percentile(r_cytoIntensityMean_segment_std_array,10);
    r_cytoIntensityMean_segment_std_25th_percentile=np.percentile(r_cytoIntensityMean_segment_std_array,25);
    r_cytoIntensityMean_segment_std_50th_percentile=np.percentile(r_cytoIntensityMean_segment_std_array,50);
    r_cytoIntensityMean_segment_std_75th_percentile=np.percentile(r_cytoIntensityMean_segment_std_array,75);
    r_cytoIntensityMean_segment_std_90th_percentile=np.percentile(r_cytoIntensityMean_segment_std_array,90);
    dict_r_cytoIntensityMean_segment_std = {}
    dict_r_cytoIntensityMean_segment_std['10th'] = r_cytoIntensityMean_segment_std_10th_percentile;
    dict_r_cytoIntensityMean_segment_std['25th'] = r_cytoIntensityMean_segment_std_25th_percentile;
    dict_r_cytoIntensityMean_segment_std['50th'] = r_cytoIntensityMean_segment_std_50th_percentile; 
    dict_r_cytoIntensityMean_segment_std['75th'] = r_cytoIntensityMean_segment_std_75th_percentile;
    dict_r_cytoIntensityMean_segment_std['90th'] = r_cytoIntensityMean_segment_std_90th_percentile;   
    dict_data['r_cytoIntensityMean_segment_std'] = dict_r_cytoIntensityMean_segment_std;  
      
    b_cytoIntensityMean_segment_mean_10th_percentile=np.percentile(b_cytoIntensityMean_segment_mean_array,10);
    b_cytoIntensityMean_segment_mean_25th_percentile=np.percentile(b_cytoIntensityMean_segment_mean_array,25);
    b_cytoIntensityMean_segment_mean_50th_percentile=np.percentile(b_cytoIntensityMean_segment_mean_array,50);
    b_cytoIntensityMean_segment_mean_75th_percentile=np.percentile(b_cytoIntensityMean_segment_mean_array,75);
    b_cytoIntensityMean_segment_mean_90th_percentile=np.percentile(b_cytoIntensityMean_segment_mean_array,90);   
    dict_b_cytoIntensityMean_segment_mean = {}
    dict_b_cytoIntensityMean_segment_mean['10th'] = b_cytoIntensityMean_segment_mean_10th_percentile;
    dict_b_cytoIntensityMean_segment_mean['25th'] = b_cytoIntensityMean_segment_mean_25th_percentile;
    dict_b_cytoIntensityMean_segment_mean['50th'] = b_cytoIntensityMean_segment_mean_50th_percentile; 
    dict_b_cytoIntensityMean_segment_mean['75th'] = b_cytoIntensityMean_segment_mean_75th_percentile;
    dict_b_cytoIntensityMean_segment_mean['90th'] = b_cytoIntensityMean_segment_mean_90th_percentile;   
    dict_data['b_cytoIntensityMean_segment_mean'] = dict_b_cytoIntensityMean_segment_mean;
    
    b_cytoIntensityMean_segment_std_10th_percentile=np.percentile(b_cytoIntensityMean_segment_std_array,10);
    b_cytoIntensityMean_segment_std_25th_percentile=np.percentile(b_cytoIntensityMean_segment_std_array,25);
    b_cytoIntensityMean_segment_std_50th_percentile=np.percentile(b_cytoIntensityMean_segment_std_array,50);
    b_cytoIntensityMean_segment_std_75th_percentile=np.percentile(b_cytoIntensityMean_segment_std_array,75);
    b_cytoIntensityMean_segment_std_90th_percentile=np.percentile(b_cytoIntensityMean_segment_std_array,90);      
    dict_b_cytoIntensityMean_segment_std = {}
    dict_b_cytoIntensityMean_segment_std['10th'] = b_cytoIntensityMean_segment_std_10th_percentile;
    dict_b_cytoIntensityMean_segment_std['25th'] = b_cytoIntensityMean_segment_std_25th_percentile;
    dict_b_cytoIntensityMean_segment_std['50th'] = b_cytoIntensityMean_segment_std_50th_percentile; 
    dict_b_cytoIntensityMean_segment_std['75th'] = b_cytoIntensityMean_segment_std_75th_percentile;
    dict_b_cytoIntensityMean_segment_std['90th'] = b_cytoIntensityMean_segment_std_90th_percentile;   
    dict_data['b_cytoIntensityMean_segment_std'] = dict_b_cytoIntensityMean_segment_std;
                 
    collection_saved.insert_one(dict_data);  
     
  exit(); 
  
  
  
  
  
