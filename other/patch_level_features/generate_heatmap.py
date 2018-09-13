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
    print "usage:python generate_heatmap.py config.json";
    exit(); 
   
  print " --- read config.json file ---" ;
  config_json_file = sys.argv[-1];  
  with open(config_json_file) as json_data:
    d = json.load(json_data);        
    image_list_file = d['image_list'];  
    print image_list_file;    
    if not os.path.isfile(image_list_file):
      print "image list_file is not available."
      exit();   
    patch_size =  d['patch_size'];   
    db_host = d['db_host'];
    db_port = d['db_port'];
    db_name1 = d['db_name1']; 
    db_name2 = d['db_name2'];
    print image_list_file,patch_size,db_host,db_port,db_name1,db_name2;
  #exit();
  
  print '--- read image_user_list file ---- ';  
  index=0;
  image_list=[];  
  with open(image_list_file, 'r') as my_file:
    reader = csv.reader(my_file, delimiter=',')
    my_list = list(reader);
    for each_row in my_list: 
      tmp_array=[[],[]]
      print each_row[0];
      tmp_array[0]=each_row[0];   
      tmp_array[1]=each_row[1];           
      image_list.append(tmp_array);                
  print "total rows from image_list file is %d " % len(image_list) ; 
  print image_list;
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
  
  patch_level_dataset = db2.patch_level_features_batch_2;  
  #patch_level_dataset = db2.patch_level_features_add; 
  
  region_type="tumor";
  #region_type="non_tumor";
  #region_type="all";
    
  ###################################################################### 
  def save2Meta(case_id,feature_name):     
    subject_id = case_id;  
    if(subject_id[0:4] == "TCGA"):
      subject_id = case_id.substr(0,12);     
    #print case_id,subject_id;       
    
    dict_meta = collections.OrderedDict();    
    dict_img = {}
    dict_img['case_id'] = case_id 
    dict_img['subject_id'] = subject_id
    
    if(feature_name=="percent_nuclear_material"):      
      analysis_execution_id ="PL_percent_nuclear_material_"+region_type;        
    elif (feature_name=="grayscale_patch_mean"):      
      analysis_execution_id ="PL_grayscale_patch_mean_"+region_type;    
    elif (feature_name=="grayscale_patch_std"):      
      analysis_execution_id ="PL_grayscale_patch_std_"+region_type;
    elif (feature_name=="Hematoxylin_patch_mean"):      
      analysis_execution_id ="PL_Hematoxylin_patch_mean_"+region_type;   
    elif (feature_name=="Hematoxylin_patch_std"):      
      analysis_execution_id ="PL_Hematoxylin_patch_std_"+region_type;     
    elif (feature_name=="grayscale_segment_mean"):      
      analysis_execution_id ="PL_grayscale_segment_mean_"+region_type;    
    elif (feature_name=="grayscale_segment_std"):      
      analysis_execution_id ="PL_grayscale_segment_std_"+region_type;
    elif (feature_name=="Hematoxylin_segment_mean"):      
      analysis_execution_id ="PL_Hematoxylin_segment_mean_"+region_type;    
    elif (feature_name=="Hematoxylin_segment_std"):      
      analysis_execution_id ="PL_Hematoxylin_segment_std_"+region_type;              
    elif (feature_name=="Flatness_segment_mean"):      
      analysis_execution_id ="PL_Flatness_mean_"+region_type;     
    elif (feature_name=="Flatness_segment_std"):      
      analysis_execution_id ="PL_Flatness_std_"+region_type;  
    elif (feature_name=="Perimeter_segment_mean"):      
      analysis_execution_id ="PL_Perimeter_mean_"+region_type;     
    elif (feature_name=="Perimeter_segment_std"):
      analysis_execution_id ="PL_Perimeter_std_"+region_type;      
    elif (feature_name=="Circularity_segment_mean"):      
      analysis_execution_id ="PL_Circularity_mean_"+region_type;     
    elif (feature_name=="Circularity_segment_std"):      
      analysis_execution_id ="PL_Circularity_std_"+region_type;     
    elif (feature_name=="r_GradientMean_segment_mean"):      
      analysis_execution_id ="PL_r_GradientMean_mean_"+region_type;      
    elif (feature_name=="r_GradientMean_segment_std"):      
      analysis_execution_id ="PL_r_GradientMean_std_"+region_type;      
    elif (feature_name=="b_GradientMean_segment_mean"):      
      analysis_execution_id ="PL_b_GradientMean_mean_"+region_type;      
    elif (feature_name=="b_GradientMean_segment_std"):      
      analysis_execution_id ="PL_b_GradientMean_std_"+region_type;      
    elif (feature_name=="r_cytoIntensityMean_segment_mean"):      
      analysis_execution_id ="PL_r_cytoIntensityMean_mean_"+region_type;      
    elif (feature_name=="r_cytoIntensityMean_segment_std"):      
      analysis_execution_id ="PL_r_cytoIntensityMean_std_"+region_type;     
    elif (feature_name=="b_cytoIntensityMean_segment_mean"):      
      analysis_execution_id ="PL_b_cytoIntensityMean_mean_"+region_type;      
    elif (feature_name=="b_cytoIntensityMean_segment_std"):     
      analysis_execution_id ="PL_b_cytoIntensityMean_std_"+region_type;       
   
    dict_meta['color'] = 'yellow'
    dict_meta['title'] = analysis_execution_id
    dict_meta['image'] = dict_img

    dict_meta_provenance = {}
    dict_meta_provenance['analysis_execution_id'] = analysis_execution_id;
    dict_meta_provenance['study_id'] = 'SEER'
    dict_meta_provenance['type'] = 'computer'    
    dict_meta['provenance'] = dict_meta_provenance

    dict_meta['submit_date'] = datetime.datetime.now()
    dict_meta['randval'] = random.uniform(0,1)
    record_count=metadata.find({"image.case_id":case_id,
                                 "provenance.analysis_execution_id": analysis_execution_id
                               }).count();
    if (record_count ==0):                             
      metadata.insert_one(dict_meta);
  ######################################################################
  
  ###################################################################### 
  def save2Objects(case_id,feature_name,patch_size,patch_polygon,feature_value):  
    subject_id = case_id;  
    if(subject_id[0:4] == "TCGA"):
      subject_id = case_id.substr(0,12);    
    n_heat = 1
    heat_list = ['percent_nuclear_material']
    weight_list = ['0.5']
    slide_type = 'SEER';
    
    metric_value = feature_value; 
    
    if(feature_name=="percent_nuclear_material"):   
      analysis_execution_id ="PL_percent_nuclear_material_"+region_type;        
    elif (feature_name=="grayscale_patch_mean"):      
      analysis_execution_id ="PL_grayscale_patch_mean_"+region_type;      
    elif (feature_name=="grayscale_patch_std"):      
      analysis_execution_id ="PL_grayscale_patch_std_"+region_type; 
    elif (feature_name=="Hematoxylin_patch_mean"):      
      analysis_execution_id ="PL_Hematoxylin_patch_mean_"+region_type;      
    elif (feature_name=="Hematoxylin_patch_std"):      
      analysis_execution_id ="PL_Hematoxylin_patch_std_"+region_type;   
    elif (feature_name=="grayscale_segment_mean"):      
      analysis_execution_id ="PL_grayscale_segment_mean_"+region_type;      
    elif (feature_name=="grayscale_segment_std"):      
      analysis_execution_id ="PL_grayscale_segment_std_"+region_type; 
    elif (feature_name=="Hematoxylin_segment_mean"):      
      analysis_execution_id ="PL_Hematoxylin_segment_mean_"+region_type;      
    elif (feature_name=="Hematoxylin_segment_std"):      
      analysis_execution_id ="PL_Hematoxylin_segment_std_"+region_type;
    elif (feature_name=="Flatness_segment_mean"):      
      analysis_execution_id ="PL_Flatness_mean_"+region_type;     
    elif (feature_name=="Flatness_segment_std"):      
      analysis_execution_id ="PL_Flatness_std_"+region_type;  
    elif (feature_name=="Perimeter_segment_mean"):      
      analysis_execution_id ="PL_Perimeter_mean_"+region_type;     
    elif (feature_name=="Perimeter_segment_std"):
      analysis_execution_id ="PL_Perimeter_std_"+region_type;      
    elif (feature_name=="Circularity_segment_mean"):      
      analysis_execution_id ="PL_Circularity_mean_"+region_type;     
    elif (feature_name=="Circularity_segment_std"):      
      analysis_execution_id ="PL_Circularity_std_"+region_type;     
    elif (feature_name=="r_GradientMean_segment_mean"):      
      analysis_execution_id ="PL_r_GradientMean_mean_"+region_type;      
    elif (feature_name=="r_GradientMean_segment_std"):      
      analysis_execution_id ="PL_r_GradientMean_std_"+region_type;      
    elif (feature_name=="b_GradientMean_segment_mean"):      
      analysis_execution_id ="PL_b_GradientMean_mean_"+region_type;      
    elif (feature_name=="b_GradientMean_segment_std"):      
      analysis_execution_id ="PL_b_GradientMean_std_"+region_type;      
    elif (feature_name=="r_cytoIntensityMean_segment_mean"):      
      analysis_execution_id ="PL_r_cytoIntensityMean_mean_"+region_type;      
    elif (feature_name=="r_cytoIntensityMean_segment_std"):      
      analysis_execution_id ="PL_r_cytoIntensityMean_std_"+region_type;     
    elif (feature_name=="b_cytoIntensityMean_segment_mean"):      
      analysis_execution_id ="PL_b_cytoIntensityMean_mean_"+region_type;      
    elif (feature_name=="b_cytoIntensityMean_segment_std"):     
      analysis_execution_id ="PL_b_cytoIntensityMean_std_"+region_type; 
           
    dict_img = {}
    dict_img['case_id'] = case_id
    dict_img['subject_id'] = subject_id

    dict_analysis = {}
    dict_analysis['study_id'] = slide_type
    dict_analysis['execution_id'] = analysis_execution_id
    dict_analysis['source'] = 'computer'
    dict_analysis['computation'] = 'heatmap'  
    
    patch_area = patch_size * patch_size;    
    x1=patch_polygon[0][0];
    y1=patch_polygon[0][1];
    x2=patch_polygon[2][0];
    y2=patch_polygon[2][1];
    x=(x1+x2)/2.0;
    y=(y1+y2)/2.0;
    
    #dict_patch = {}
    dict_patch = collections.OrderedDict();
    dict_patch['type'] = 'Feature'
    dict_patch['parent_id'] = 'self'
    dict_patch['footprint'] = patch_area
    dict_patch['x'] = x
    dict_patch['y'] = y
    dict_patch['normalized'] = 'true'
    dict_patch['object_type'] = 'heatmap'    
    dict_patch['bbox'] = [x1, y1, x2, y2]

    dict_geo = {}
    dict_geo['type'] = 'Polygon'
    dict_geo['coordinates'] = [[[x1, y1], [x2, y1], [x2, y2], [x1, y2], [x1, y1]]]
    dict_patch['geometry'] = dict_geo

    dict_prop = {}
    dict_prop['metric_value'] = metric_value;
    dict_prop['metric_type'] = 'tile_dice'
    dict_prop['human_mark'] = -1

    dict_multiheat = {}
    dict_multiheat['human_weight'] = -1
    dict_multiheat['weight_array'] = weight_list
    dict_multiheat['heatname_array'] = heat_list
    dict_multiheat['metric_array'] = 1

    dict_prop['multiheat_param'] = dict_multiheat
    dict_patch['properties'] = dict_prop

    dict_provenance = {}
    dict_provenance['image'] = dict_img
    dict_provenance['analysis'] = dict_analysis
    dict_patch['provenance'] = dict_provenance

    dict_patch['date'] = datetime.datetime.now();
    #print dict_patch;
    objects.insert_one(dict_patch);  
  ######################################################################
 
  ######################################################################
  def removeAllHeatmaps_tumor(case_id):  
    metadata.remove({"image.case_id":case_id,
                     "provenance.analysis_execution_id":"PL_percent_nuclear_material_tumor"}); 
    metadata.remove({"image.case_id":case_id,
                     "provenance.analysis_execution_id":"PL_grayscale_patch_mean_tumor"});    
    metadata.remove({"image.case_id":case_id,
                     "provenance.analysis_execution_id":"PL_grayscale_patch_std_tumor"});
    metadata.remove({"image.case_id":case_id,
                     "provenance.analysis_execution_id":"PL_Hematoxylin_patch_mean_tumor"});                                                   
    metadata.remove({"image.case_id":case_id,
                     "provenance.analysis_execution_id":"PL_Hematoxylin_patch_std_tumor"});
    metadata.remove({"image.case_id":case_id,
                     "provenance.analysis_execution_id":"PL_grayscale_segment_mean_tumor"});
    metadata.remove({"image.case_id":case_id,
                     "provenance.analysis_execution_id":"PL_grayscale_segment_std_tumor"});
    metadata.remove({"image.case_id":case_id,
                     "provenance.analysis_execution_id":"PL_Hematoxylin_segment_mean_tumor"});
    metadata.remove({"image.case_id":case_id,
                     "provenance.analysis_execution_id":"PL_Hematoxylin_segment_std_tumor"});
                        
    objects.remove({"provenance.image.case_id":case_id,
                     "provenance.analysis.execution_id":"PL_percent_nuclear_material_tumor"});                       
    objects.remove({"provenance.image.case_id":case_id,
                     "provenance.analysis.execution_id":"PL_grayscale_patch_mean_tumor"});
    objects.remove({"provenance.image.case_id":case_id,
                     "provenance.analysis.execution_id":"PL_grayscale_patch_std_tumor"});
    objects.remove({"provenance.image.case_id":case_id,
                     "provenance.analysis.execution_id":"PL_Hematoxylin_patch_mean_tumor"});                       
    objects.remove({"provenance.image.case_id":case_id,
                     "provenance.analysis.execution_id":"PL_Hematoxylin_patch_std_tumor"});
    objects.remove({"provenance.image.case_id":case_id,
                     "provenance.analysis.execution_id":"PL_grayscale_segment_mean_tumor"});
    objects.remove({"provenance.image.case_id":case_id,
                     "provenance.analysis.execution_id":"PL_grayscale_segment_std_tumor"});                       
    objects.remove({"provenance.image.case_id":case_id,
                     "provenance.analysis.execution_id":"PL_Hematoxylin_segment_mean_tumor"});
    objects.remove({"provenance.image.case_id":case_id,
                     "provenance.analysis.execution_id":"PL_Hematoxylin_segment_std_tumor"});                       
  ######################################################################
  
  ######################################################################
  def removeAllHeatmaps_non_tumor(case_id):  
    metadata.remove({"image.case_id":case_id,
                     "provenance.analysis_execution_id":"PL_percent_nuclear_material_non_tumor"}); 
    metadata.remove({"image.case_id":case_id,
                     "provenance.analysis_execution_id":"PL_grayscale_patch_mean_non_tumor"});    
    metadata.remove({"image.case_id":case_id,
                     "provenance.analysis_execution_id":"PL_grayscale_patch_std_non_tumor"});
    metadata.remove({"image.case_id":case_id,
                     "provenance.analysis_execution_id":"PL_Hematoxylin_patch_mean_non_tumor"});                                                   
    metadata.remove({"image.case_id":case_id,
                     "provenance.analysis_execution_id":"PL_Hematoxylin_patch_std_non_tumor"});
    metadata.remove({"image.case_id":case_id,
                     "provenance.analysis_execution_id":"PL_grayscale_segment_mean_non_tumor"});
    metadata.remove({"image.case_id":case_id,
                     "provenance.analysis_execution_id":"PL_grayscale_segment_std_non_tumor"});
    metadata.remove({"image.case_id":case_id,
                     "provenance.analysis_execution_id":"PL_Hematoxylin_segment_mean_non_tumor"});
    metadata.remove({"image.case_id":case_id,
                     "provenance.analysis_execution_id":"PL_Hematoxylin_segment_std_non_tumor"});
                        
    objects.remove({"provenance.image.case_id":case_id,
                     "provenance.analysis.execution_id":"PL_percent_nuclear_material_non_tumor"});                       
    objects.remove({"provenance.image.case_id":case_id,
                     "provenance.analysis.execution_id":"PL_grayscale_patch_mean_non_tumor"});
    objects.remove({"provenance.image.case_id":case_id,
                     "provenance.analysis.execution_id":"PL_grayscale_patch_std_non_tumor"});
    objects.remove({"provenance.image.case_id":case_id,
                     "provenance.analysis.execution_id":"PL_Hematoxylin_patch_mean_non_tumor"});                       
    objects.remove({"provenance.image.case_id":case_id,
                     "provenance.analysis.execution_id":"PL_Hematoxylin_patch_std_non_tumor"});
    objects.remove({"provenance.image.case_id":case_id,
                     "provenance.analysis.execution_id":"PL_grayscale_segment_mean_non_tumor"});
    objects.remove({"provenance.image.case_id":case_id,
                     "provenance.analysis.execution_id":"PL_grayscale_segment_std_non_tumor"});                       
    objects.remove({"provenance.image.case_id":case_id,
                     "provenance.analysis.execution_id":"PL_Hematoxylin_segment_mean_non_tumor"});
    objects.remove({"provenance.image.case_id":case_id,
                     "provenance.analysis.execution_id":"PL_Hematoxylin_segment_std_non_tumor"});                       
  ######################################################################                    
  
                                                                     
  print '--- process image_list  ---- ';   
  for item in image_list:  
    case_id=item[0];
    user=item[1];
    
    print "=========== "+ str(case_id) + " ====== " +str(user) + "  ============";
        
    removeAllHeatmaps_tumor(case_id);    
    #removeAllHeatmaps_non_tumor(case_id);    
    
    record_count=patch_level_dataset.find({"case_id":case_id,
                                           "user":user,
                                           "tumorFlag":region_type,
                                           "percent_nuclear_material": { "$gte": 0.0 }}).count();        
    if(record_count>0):
      save2Meta(case_id,"percent_nuclear_material");    
      save2Meta(case_id,"grayscale_patch_mean");
      save2Meta(case_id,"grayscale_patch_std");
      save2Meta(case_id,"Hematoxylin_patch_mean");
      save2Meta(case_id,"Hematoxylin_patch_std");    
      save2Meta(case_id,"grayscale_segment_mean");
      save2Meta(case_id,"grayscale_segment_std");
      save2Meta(case_id,"Hematoxylin_segment_mean");
      save2Meta(case_id,"Hematoxylin_segment_std");            
      save2Meta(case_id,"Flatness_segment_mean");
      save2Meta(case_id,"Flatness_segment_std");
      save2Meta(case_id,"Perimeter_segment_mean");
      save2Meta(case_id,"Perimeter_segment_std");
      save2Meta(case_id,"Circularity_segment_mean");
      save2Meta(case_id,"Circularity_segment_std");
      save2Meta(case_id,"r_GradientMean_segment_mean");
      save2Meta(case_id,"r_GradientMean_segment_std");
      save2Meta(case_id,"b_GradientMean_segment_mean");
      save2Meta(case_id,"b_GradientMean_segment_std");
      save2Meta(case_id,"r_cytoIntensityMean_segment_mean");
      save2Meta(case_id,"r_cytoIntensityMean_segment_std");
      save2Meta(case_id,"b_cytoIntensityMean_segment_mean");
      save2Meta(case_id,"b_cytoIntensityMean_segment_std");       
    else:
      continue;   
        
    min_grayscale_patch_mean=0.0;
    max_grayscale_patch_mean=0.0;
    min_grayscale_patch_std=0.0;
    max_grayscale_patch_std=0.0;    
    min_Hematoxylin_patch_mean=0.0;
    max_Hematoxylin_patch_mean=0.0;
    min_Hematoxylin_patch_std=0.0;
    max_Hematoxylin_patch_std=0.0;  
    
    for record in patch_level_dataset.find({"case_id":case_id,"user":user,"tumorFlag":region_type,"percent_nuclear_material": { "$gte": 0.0 }},
                                          {"grayscale_patch_mean":1,"_id":0}).sort("grayscale_patch_mean",1).limit(1):
      min_grayscale_patch_mean = record["grayscale_patch_mean"];
      break;                                                          
    for record in patch_level_dataset.find({"case_id":case_id,"user":user,"tumorFlag":region_type,"percent_nuclear_material": { "$gte": 0.0 }},
                                           {"grayscale_patch_mean":1,"_id":0}).sort("grayscale_patch_mean",-1).limit(1):
      max_grayscale_patch_mean = record["grayscale_patch_mean"];
      break;                                                            
    for record in patch_level_dataset.find({"case_id":case_id,"user":user,"tumorFlag":region_type,"percent_nuclear_material": { "$gte": 0.0 }},
                                          {"grayscale_patch_std":1,"_id":0}).sort("grayscale_patch_std",1).limit(1):
      min_grayscale_patch_std = record["grayscale_patch_std"];
      break;                                                            
    for record in  patch_level_dataset.find({"case_id":case_id,"user":user,"tumorFlag":region_type,"percent_nuclear_material": { "$gte": 0.0 }},
                                            {"grayscale_patch_std":1,"_id":0}).sort("grayscale_patch_std",-1).limit(1):  
      max_grayscale_patch_std = record["grayscale_patch_std"];
      break;                                                                                                                               
    for record in patch_level_dataset.find({"case_id":case_id,"user":user,"tumorFlag":region_type,"percent_nuclear_material": { "$gte": 0.0 }},
                                           {"Hematoxylin_patch_mean":1,"_id":0}).sort("Hematoxylin_patch_mean",1).limit(1):
      min_Hematoxylin_patch_mean = record["Hematoxylin_patch_mean"];
      break;                                                            
    for record in patch_level_dataset.find({"case_id":case_id,"user":user,"tumorFlag":region_type,"percent_nuclear_material": { "$gte": 0.0 }},
                                           {"Hematoxylin_patch_mean":1,"_id":0}).sort("Hematoxylin_patch_mean",-1).limit(1):
      max_Hematoxylin_patch_mean = record["Hematoxylin_patch_mean"];
      break;                                       
    for record in patch_level_dataset.find({"case_id":case_id,"user":user,"tumorFlag":region_type,"percent_nuclear_material": { "$gte": 0.0 }},
                                           {"Hematoxylin_patch_std":1,"_id":0}).sort("Hematoxylin_patch_std",1).limit(1):
      min_Hematoxylin_patch_std = record["Hematoxylin_patch_std"];
      break;                                                            
    for record in patch_level_dataset.find({"case_id":case_id,"user":user,"tumorFlag":region_type,"percent_nuclear_material": { "$gte": 0.0 }},
                                           {"Hematoxylin_patch_std":1,"_id":0}).sort("Hematoxylin_patch_std",-1).limit(1):  
      max_Hematoxylin_patch_std = record["Hematoxylin_patch_std"];
      break;                                                                  
    print " --min_grayscale_patch_mean,max_grayscale_patch_mean,min_grayscale_patch_std,max_grayscale_patch_std,min_Hematoxylin_patch_mean,max_Hematoxylin_patch_mean,min_Hematoxylin_patch_std,max_Hematoxylin_patch_std --";
    print min_grayscale_patch_mean,max_grayscale_patch_mean,min_grayscale_patch_std,max_grayscale_patch_std,min_Hematoxylin_patch_mean,max_Hematoxylin_patch_mean,min_Hematoxylin_patch_std,max_Hematoxylin_patch_std;
    
    min_grayscale_segment_mean=0.0;
    min_grayscale_segment_std=0.0;
    min_Hematoxylin_segment_mean=0.0;
    min_Hematoxylin_segment_std=0.0;    
    max_grayscale_segment_mean=0.0;
    max_grayscale_segment_std=0.0;
    max_Hematoxylin_segment_mean=0.0;
    max_Hematoxylin_segment_std=0.0;
    
    for record in patch_level_dataset.find({"case_id":case_id,"user":user,"tumorFlag":region_type,"grayscale_segment_mean": { "$ne": "n/a" }},
                                          {"grayscale_segment_mean":1,"_id":0}).sort("grayscale_segment_mean",1).limit(1):
      min_grayscale_segment_mean = record["grayscale_segment_mean"];
      break;                                                          
    for record in patch_level_dataset.find({"case_id":case_id,"user":user,"tumorFlag":region_type,"grayscale_segment_mean": { "$ne": "n/a" }},
                                           {"grayscale_segment_mean":1,"_id":0}).sort("grayscale_segment_mean",-1).limit(1):
      max_grayscale_segment_mean = record["grayscale_segment_mean"];
      break;   
    for record in patch_level_dataset.find({"case_id":case_id,"user":user,"tumorFlag":region_type,"grayscale_segment_std": { "$ne": "n/a" }},
                                          {"grayscale_segment_std":1,"_id":0}).sort("grayscale_segment_std",1).limit(1):
      min_grayscale_segment_std = record["grayscale_segment_std"];
      break;                                                          
    for record in patch_level_dataset.find({"case_id":case_id,"user":user,"tumorFlag":region_type,"grayscale_segment_std": { "$ne": "n/a" }},
                                           {"grayscale_segment_std":1,"_id":0}).sort("grayscale_segment_std",-1).limit(1):
      max_grayscale_segment_std = record["grayscale_segment_std"];
      break;    
    for record in patch_level_dataset.find({"case_id":case_id,"user":user,"tumorFlag":region_type,"Hematoxylin_segment_mean": { "$ne": "n/a" }},
                                          {"Hematoxylin_segment_mean":1,"_id":0}).sort("Hematoxylin_segment_mean",1).limit(1):
      min_Hematoxylin_segment_mean = record["Hematoxylin_segment_mean"];
      break;                                                          
    for record in patch_level_dataset.find({"case_id":case_id,"user":user,"tumorFlag":region_type,"Hematoxylin_segment_mean": { "$ne": "n/a" }},
                                           {"Hematoxylin_segment_mean":1,"_id":0}).sort("Hematoxylin_segment_mean",-1).limit(1):
      max_Hematoxylin_segment_mean = record["Hematoxylin_segment_mean"];
      break;
    for record in patch_level_dataset.find({"case_id":case_id,"user":user,"tumorFlag":region_type,"Hematoxylin_segment_std": { "$ne": "n/a" }},
                                          {"Hematoxylin_segment_std":1,"_id":0}).sort("Hematoxylin_segment_std",1).limit(1):
      min_Hematoxylin_segment_std = record["Hematoxylin_segment_std"];
      break;                                                          
    for record in patch_level_dataset.find({"case_id":case_id,"user":user,"tumorFlag":region_type,"Hematoxylin_segment_std": { "$ne": "n/a" }},
                                           {"Hematoxylin_segment_std":1,"_id":0}).sort("Hematoxylin_segment_std",-1).limit(1):
      max_Hematoxylin_segment_std = record["Hematoxylin_segment_std"];
      break;    
    print "min_grayscale_segment_mean,max_grayscale_segment_mean,min_grayscale_segment_std,max_grayscale_segment_std,min_Hematoxylin_segment_mean,max_Hematoxylin_segment_mean,min_Hematoxylin_segment_std,max_Hematoxylin_segment_std";  
    print min_grayscale_segment_mean,max_grayscale_segment_mean,min_grayscale_segment_std,max_grayscale_segment_std,min_Hematoxylin_segment_mean,max_Hematoxylin_segment_mean,min_Hematoxylin_segment_std,max_Hematoxylin_segment_std;  
    
    min_Flatness_segment_mean=0.0;
    max_Flatness_segment_mean=0.0;    
    min_Flatness_segment_std=0.0;
    max_Flatness_segment_std=0.0;    
    min_Perimeter_segment_mean=0.0;
    max_Perimeter_segment_mean=0.0;    
    min_Perimeter_segment_std=0.0;
    max_Perimeter_segment_std=0.0;
    for record in patch_level_dataset.find({"case_id":case_id,"user":user,"tumorFlag":region_type,"Flatness_segment_mean": { "$ne": "n/a" }},
                                          {"Flatness_segment_mean":1,"_id":0}).sort("Flatness_segment_mean",1).limit(1):
      min_Flatness_segment_mean = record["Flatness_segment_mean"];
      break;                                                          
    for record in patch_level_dataset.find({"case_id":case_id,"user":user,"tumorFlag":region_type,"Flatness_segment_mean": { "$ne": "n/a" }},
                                           {"Flatness_segment_mean":1,"_id":0}).sort("Flatness_segment_mean",-1).limit(1):
      max_Flatness_segment_mean = record["Flatness_segment_mean"];
      break;      
    for record in patch_level_dataset.find({"case_id":case_id,"user":user,"tumorFlag":region_type,"Flatness_segment_std": { "$ne": "n/a" }},
                                          {"Flatness_segment_std":1,"_id":0}).sort("Flatness_segment_std",1).limit(1):
      min_Flatness_segment_std = record["Flatness_segment_std"];
      break;                                                          
    for record in patch_level_dataset.find({"case_id":case_id,"user":user,"tumorFlag":region_type,"Flatness_segment_std": { "$ne": "n/a" }},
                                           {"Flatness_segment_std":1,"_id":0}).sort("Flatness_segment_std",-1).limit(1):
      max_Flatness_segment_std = record["Flatness_segment_std"];
      break;         
    for record in patch_level_dataset.find({"case_id":case_id,"user":user,"tumorFlag":region_type,"Perimeter_segment_mean": { "$ne": "n/a" }},
                                          {"Perimeter_segment_mean":1,"_id":0}).sort("Perimeter_segment_mean",1).limit(1):
      min_Perimeter_segment_mean = record["Perimeter_segment_mean"];
      break;                                                          
    for record in patch_level_dataset.find({"case_id":case_id,"user":user,"tumorFlag":region_type,"Perimeter_segment_mean": { "$ne": "n/a" }},
                                           {"Perimeter_segment_mean":1,"_id":0}).sort("Perimeter_segment_mean",-1).limit(1):
      max_Perimeter_segment_mean = record["Perimeter_segment_mean"];
      break;      
    for record in patch_level_dataset.find({"case_id":case_id,"user":user,"tumorFlag":region_type,"Perimeter_segment_std": { "$ne": "n/a" }},
                                          {"Perimeter_segment_std":1,"_id":0}).sort("Perimeter_segment_std",1).limit(1):
      min_Perimeter_segment_std = record["Perimeter_segment_std"];
      break;                                                          
    for record in patch_level_dataset.find({"case_id":case_id,"user":user,"tumorFlag":region_type,"Perimeter_segment_std": { "$ne": "n/a" }},
                                           {"Perimeter_segment_std":1,"_id":0}).sort("Perimeter_segment_std",-1).limit(1):
      max_Perimeter_segment_std = record["Perimeter_segment_std"];
      break;       
    print "min_Flatness_segment_mean,max_Flatness_segment_mean,min_Flatness_segment_std,max_Flatness_segment_std,min_Perimeter_segment_mean,max_Perimeter_segment_mean,min_Perimeter_segment_std,max_Perimeter_segment_std"; 
    print min_Flatness_segment_mean,max_Flatness_segment_mean,min_Flatness_segment_std,max_Flatness_segment_std,min_Perimeter_segment_mean,max_Perimeter_segment_mean,min_Perimeter_segment_std,max_Perimeter_segment_std;  
    
       
    min_Circularity_segment_mean=0.0;
    min_Circularity_segment_std=0.0;
    max_Circularity_segment_mean=0.0;
    max_Circularity_segment_std =0.0; 
    for record in patch_level_dataset.find({"case_id":case_id,"user":user,"tumorFlag":region_type,"Circularity_segment_mean": { "$ne": "n/a" }},
                                          {"Circularity_segment_mean":1,"_id":0}).sort("Circularity_segment_mean",1).limit(1):
      min_Circularity_segment_mean = record["Circularity_segment_mean"];
      break;                                                          
    for record in patch_level_dataset.find({"case_id":case_id,"user":user,"tumorFlag":region_type,"Circularity_segment_mean": { "$ne": "n/a" }},
                                           {"Circularity_segment_mean":1,"_id":0}).sort("Circularity_segment_mean",-1).limit(1):
      max_Circularity_segment_mean = record["Circularity_segment_mean"];
      break;
    for record in patch_level_dataset.find({"case_id":case_id,"user":user,"tumorFlag":region_type,"Circularity_segment_std": { "$ne": "n/a" }},
                                          {"Circularity_segment_std":1,"_id":0}).sort("Circularity_segment_std",1).limit(1):
      min_Circularity_segment_std = record["Circularity_segment_std"];
      break;                                                          
    for record in patch_level_dataset.find({"case_id":case_id,"user":user,"tumorFlag":region_type,"Circularity_segment_std": { "$ne": "n/a" }},
                                           {"Circularity_segment_std":1,"_id":0}).sort("Circularity_segment_std",-1).limit(1):
      max_Circularity_segment_std = record["Circularity_segment_std"];
      break; 
    print "min_Circularity_segment_mean,max_Circularity_segment_mean,min_Circularity_segment_std,max_Circularity_segment_std"; 
    print min_Circularity_segment_mean,max_Circularity_segment_mean,min_Circularity_segment_std,max_Circularity_segment_std;  
    
    
    min_r_GradientMean_segment_mean=0.0;
    min_r_GradientMean_segment_std=0.0;
    min_b_GradientMean_segment_mean=0.0;
    min_b_GradientMean_segment_std=0.0;
    max_r_GradientMean_segment_mean=0.0;
    max_r_GradientMean_segment_std=0.0;
    max_b_GradientMean_segment_mean=0.0;
    max_b_GradientMean_segment_std=0.0;
    for record in patch_level_dataset.find({"case_id":case_id,"user":user,"tumorFlag":region_type,"r_GradientMean_segment_mean": { "$ne": "n/a" }},
                                          {"r_GradientMean_segment_mean":1,"_id":0}).sort("r_GradientMean_segment_mean",1).limit(1):
      min_r_GradientMean_segment_mean = record["r_GradientMean_segment_mean"];
      break;                                                          
    for record in patch_level_dataset.find({"case_id":case_id,"user":user,"tumorFlag":region_type,"r_GradientMean_segment_mean": { "$ne": "n/a" }},
                                           {"r_GradientMean_segment_mean":1,"_id":0}).sort("r_GradientMean_segment_mean",-1).limit(1):
      max_r_GradientMean_segment_mean = record["r_GradientMean_segment_mean"];
      break;       
    for record in patch_level_dataset.find({"case_id":case_id,"user":user,"tumorFlag":region_type,"r_GradientMean_segment_std": { "$ne": "n/a" }},
                                          {"r_GradientMean_segment_std":1,"_id":0}).sort("r_GradientMean_segment_std",1).limit(1):
      min_r_GradientMean_segment_std = record["r_GradientMean_segment_std"];
      break;                                                          
    for record in patch_level_dataset.find({"case_id":case_id,"user":user,"tumorFlag":region_type,"r_GradientMean_segment_std": { "$ne": "n/a" }},
                                           {"r_GradientMean_segment_std":1,"_id":0}).sort("r_GradientMean_segment_std",-1).limit(1):
      max_r_GradientMean_segment_std = record["r_GradientMean_segment_std"];
      break;       
    for record in patch_level_dataset.find({"case_id":case_id,"user":user,"tumorFlag":region_type,"b_GradientMean_segment_mean": { "$ne": "n/a" }},
                                          {"b_GradientMean_segment_mean":1,"_id":0}).sort("b_GradientMean_segment_mean",1).limit(1):
      min_b_GradientMean_segment_mean = record["b_GradientMean_segment_mean"];
      break;                                                          
    for record in patch_level_dataset.find({"case_id":case_id,"user":user,"tumorFlag":region_type,"b_GradientMean_segment_mean": { "$ne": "n/a" }},
                                           {"b_GradientMean_segment_mean":1,"_id":0}).sort("b_GradientMean_segment_mean",-1).limit(1):
      max_b_GradientMean_segment_mean = record["b_GradientMean_segment_mean"];
      break;      
    for record in patch_level_dataset.find({"case_id":case_id,"user":user,"tumorFlag":region_type,"b_GradientMean_segment_std": { "$ne": "n/a" }},
                                          {"b_GradientMean_segment_std":1,"_id":0}).sort("b_GradientMean_segment_std",1).limit(1):
      min_b_GradientMean_segment_std = record["b_GradientMean_segment_std"];
      break;                                                          
    for record in patch_level_dataset.find({"case_id":case_id,"user":user,"tumorFlag":region_type,"b_GradientMean_segment_std": { "$ne": "n/a" }},
                                           {"b_GradientMean_segment_std":1,"_id":0}).sort("b_GradientMean_segment_std",-1).limit(1):
      max_b_GradientMean_segment_std = record["b_GradientMean_segment_std"];
      break;    
    print "min_r_GradientMean_segment_mean,max_r_GradientMean_segment_mean,min_r_GradientMean_segment_std,max_r_GradientMean_segment_std,min_b_GradientMean_segment_mean,max_b_GradientMean_segment_mean,min_b_GradientMean_segment_std,    max_b_GradientMean_segment_std"; 
    print min_r_GradientMean_segment_mean,max_r_GradientMean_segment_mean,min_r_GradientMean_segment_std,max_r_GradientMean_segment_std,min_b_GradientMean_segment_mean,max_b_GradientMean_segment_mean,min_b_GradientMean_segment_std,    max_b_GradientMean_segment_std; 
       
    min_r_cytoIntensityMean_segment_mean=0.0;
    max_r_cytoIntensityMean_segment_mean=0.0;
    min_r_cytoIntensityMean_segment_std=0.0;
    max_r_cytoIntensityMean_segment_std=0.0;
    min_b_cytoIntensityMean_segment_mean=0.0;
    max_b_cytoIntensityMean_segment_mean=0.0;
    min_b_cytoIntensityMean_segment_std=0.0;
    max_b_cytoIntensityMean_segment_std=0.0; 
    for record in patch_level_dataset.find({"case_id":case_id,"user":user,"tumorFlag":region_type,"r_cytoIntensityMean_segment_mean": { "$ne": "n/a" }},
                                          {"r_cytoIntensityMean_segment_mean":1,"_id":0}).sort("r_cytoIntensityMean_segment_mean",1).limit(1):
      min_r_cytoIntensityMean_segment_mean = record["r_cytoIntensityMean_segment_mean"];
      break;                                                          
    for record in patch_level_dataset.find({"case_id":case_id,"user":user,"tumorFlag":region_type,"r_cytoIntensityMean_segment_mean": { "$ne": "n/a" }},
                                           {"r_cytoIntensityMean_segment_mean":1,"_id":0}).sort("r_cytoIntensityMean_segment_mean",-1).limit(1):
      max_r_cytoIntensityMean_segment_mean = record["r_cytoIntensityMean_segment_mean"];
      break;
    for record in patch_level_dataset.find({"case_id":case_id,"user":user,"tumorFlag":region_type,"r_cytoIntensityMean_segment_std": { "$ne": "n/a" }},
                                          {"r_cytoIntensityMean_segment_std":1,"_id":0}).sort("r_cytoIntensityMean_segment_std",1).limit(1):
      min_r_cytoIntensityMean_segment_std = record["r_cytoIntensityMean_segment_std"];
      break;                                                          
    for record in patch_level_dataset.find({"case_id":case_id,"user":user,"tumorFlag":region_type,"r_cytoIntensityMean_segment_std": { "$ne": "n/a" }},
                                           {"r_cytoIntensityMean_segment_std":1,"_id":0}).sort("r_cytoIntensityMean_segment_std",-1).limit(1):
      max_r_cytoIntensityMean_segment_std = record["r_cytoIntensityMean_segment_std"];
      break;
    for record in patch_level_dataset.find({"case_id":case_id,"user":user,"tumorFlag":region_type,"b_cytoIntensityMean_segment_mean": { "$ne": "n/a" }},
                                          {"b_cytoIntensityMean_segment_mean":1,"_id":0}).sort("b_cytoIntensityMean_segment_mean",1).limit(1):
      min_b_cytoIntensityMean_segment_mean = record["b_cytoIntensityMean_segment_mean"];
      break;                                                          
    for record in patch_level_dataset.find({"case_id":case_id,"user":user,"tumorFlag":region_type,"b_cytoIntensityMean_segment_mean": { "$ne": "n/a" }},
                                           {"b_cytoIntensityMean_segment_mean":1,"_id":0}).sort("b_cytoIntensityMean_segment_mean",-1).limit(1):
      max_b_cytoIntensityMean_segment_mean = record["b_cytoIntensityMean_segment_mean"];
      break; 
    for record in patch_level_dataset.find({"case_id":case_id,"user":user,"tumorFlag":region_type,"b_cytoIntensityMean_segment_std": { "$ne": "n/a" }},
                                          {"b_cytoIntensityMean_segment_std":1,"_id":0}).sort("b_cytoIntensityMean_segment_std",1).limit(1):
      min_b_cytoIntensityMean_segment_std = record["b_cytoIntensityMean_segment_std"];
      break;                                                          
    for record in patch_level_dataset.find({"case_id":case_id,"user":user,"tumorFlag":region_type,"b_cytoIntensityMean_segment_std": { "$ne": "n/a" }},
                                           {"b_cytoIntensityMean_segment_std":1,"_id":0}).sort("b_cytoIntensityMean_segment_std",-1).limit(1):
      max_b_cytoIntensityMean_segment_std = record["b_cytoIntensityMean_segment_std"];
      break; 
    print "min_r_cytoIntensityMean_segment_mean,max_r_cytoIntensityMean_segment_mean,min_r_cytoIntensityMean_segment_std,max_r_cytoIntensityMean_segment_std,min_b_cytoIntensityMean_segment_mean,max_b_cytoIntensityMean_segment_mean,    min_b_cytoIntensityMean_segment_std,max_b_cytoIntensityMean_segment_std";
    print min_r_cytoIntensityMean_segment_mean,max_r_cytoIntensityMean_segment_mean,min_r_cytoIntensityMean_segment_std,max_r_cytoIntensityMean_segment_std,min_b_cytoIntensityMean_segment_mean,max_b_cytoIntensityMean_segment_mean,    min_b_cytoIntensityMean_segment_std,max_b_cytoIntensityMean_segment_std;   
    
                  
    index1=0;
    for feature_record in patch_level_dataset.find({"case_id":case_id,
                                                     "user":user,
                                                     "tumorFlag":region_type,
                                                     "percent_nuclear_material": { "$gte": 0.0 }}):      
      image_width=feature_record["image_width"];
      image_height=feature_record["image_height"];
      patch_min_x_pixel=feature_record["patch_min_x_pixel"];
      patch_min_y_pixel=feature_record["patch_min_y_pixel"];
      patch_size=feature_record["patch_size"];           
      percent_nuclear_material=feature_record["percent_nuclear_material"];      
      percent_nuclear_material_normalized=float(percent_nuclear_material/100.0);          
      grayscale_patch_mean=feature_record["grayscale_patch_mean"];       
      grayscale_patch_mean_normalized=float(grayscale_patch_mean - min_grayscale_patch_mean)/float(max_grayscale_patch_mean-min_grayscale_patch_mean);       
      grayscale_patch_std=feature_record["grayscale_patch_std"];
      grayscale_patch_std_normalized=float(grayscale_patch_std - min_grayscale_patch_std)/float(max_grayscale_patch_std-min_grayscale_patch_std);
      
      Hematoxylin_patch_mean=feature_record["Hematoxylin_patch_mean"];      
      Hematoxylin_patch_mean_normalized=float(Hematoxylin_patch_mean - min_Hematoxylin_patch_mean)/float(max_Hematoxylin_patch_mean-min_Hematoxylin_patch_mean);
      Hematoxylin_patch_std=feature_record["Hematoxylin_patch_std"];  
      Hematoxylin_patch_std_normalized=float(Hematoxylin_patch_std - min_Hematoxylin_patch_std)/float(max_Hematoxylin_patch_std-min_Hematoxylin_patch_std);          
          
      x1=float(patch_min_x_pixel)/float(image_width);
      y1=float(patch_min_y_pixel)/float(image_height);
      x2=float(patch_min_x_pixel+patch_size)/float(image_width);
      y2=float(patch_min_y_pixel+patch_size)/float(image_height);
      tmp_patch_polygon=[[x1,y1],[x2,y1],[x2,y2],[x1,y2],[x1,y1]];      
           
      save2Objects(case_id,"percent_nuclear_material",patch_size,tmp_patch_polygon,percent_nuclear_material_normalized);            
      save2Objects(case_id,"grayscale_patch_mean",patch_size,tmp_patch_polygon,grayscale_patch_mean_normalized); 
      save2Objects(case_id,"grayscale_patch_std",patch_size,tmp_patch_polygon,grayscale_patch_std_normalized);
      save2Objects(case_id,"Hematoxylin_patch_mean",patch_size,tmp_patch_polygon,Hematoxylin_patch_mean_normalized); 
      save2Objects(case_id,"Hematoxylin_patch_std",patch_size,tmp_patch_polygon,Hematoxylin_patch_std_normalized);      
                
      index1+=1;
      print index1,percent_nuclear_material_normalized,grayscale_patch_mean_normalized,grayscale_patch_std_normalized,Hematoxylin_patch_mean_normalized,Hematoxylin_patch_std_normalized; 
      if(percent_nuclear_material_normalized>1.0 or percent_nuclear_material_normalized<0.0):
        print "wrong";
        exit();
      if(grayscale_patch_mean_normalized>1.0 or grayscale_patch_mean_normalized<0.0):
        print "wrong";
        exit();       
      if(grayscale_patch_std_normalized>1.0 or grayscale_patch_std_normalized<0.0):
        print "wrong";
        exit();
      if(Hematoxylin_patch_mean_normalized>1.0 or Hematoxylin_patch_mean_normalized<0.0):
        print "wrong";
        exit();
      if(Hematoxylin_patch_std_normalized>1.0 or Hematoxylin_patch_std_normalized<0.0):
        print "wrong";
        exit();            
    
          
    index2=0;
    for feature_record in patch_level_dataset.find({"case_id":case_id,
                                                     "user":user,
                                                     "tumorFlag":region_type,
                                                     "grayscale_segment_mean": { "$ne": "n/a" }}):      
      image_width=feature_record["image_width"];
      image_height=feature_record["image_height"];
      patch_min_x_pixel=feature_record["patch_min_x_pixel"];
      patch_min_y_pixel=feature_record["patch_min_y_pixel"];
      patch_size=feature_record["patch_size"];  
      x1=float(patch_min_x_pixel)/float(image_width);
      y1=float(patch_min_y_pixel)/float(image_height);
      x2=float(patch_min_x_pixel+patch_size)/float(image_width);
      y2=float(patch_min_y_pixel+patch_size)/float(image_height);
      tmp_patch_polygon=[[x1,y1],[x2,y1],[x2,y2],[x1,y2],[x1,y1]];    
      index2+=1;      
      
      grayscale_segment_mean=feature_record["grayscale_segment_mean"];             
      grayscale_segment_mean_normalized=float(grayscale_segment_mean - min_grayscale_segment_mean)/float(max_grayscale_segment_mean-min_grayscale_segment_mean);      
      grayscale_segment_std=feature_record["grayscale_segment_std"];
      grayscale_segment_std_normalized=float(grayscale_segment_std - min_grayscale_segment_std)/float(max_grayscale_segment_std-min_grayscale_segment_std);       
      Hematoxylin_segment_mean=feature_record["Hematoxylin_segment_mean"];
      Hematoxylin_segment_mean_normalized=float(Hematoxylin_segment_mean - min_Hematoxylin_segment_mean)/float(max_Hematoxylin_segment_mean-min_Hematoxylin_segment_mean);
      Hematoxylin_segment_std=feature_record["Hematoxylin_segment_std"];
      Hematoxylin_segment_std_normalized=float(Hematoxylin_segment_std - min_Hematoxylin_segment_std)/float(max_Hematoxylin_segment_std-min_Hematoxylin_segment_std);            
      save2Objects(case_id,"grayscale_segment_mean",patch_size,tmp_patch_polygon,grayscale_segment_mean_normalized); 
      save2Objects(case_id,"grayscale_segment_std",patch_size,tmp_patch_polygon,grayscale_segment_std_normalized);
      save2Objects(case_id,"Hematoxylin_segment_mean",patch_size,tmp_patch_polygon,Hematoxylin_segment_mean_normalized); 
      save2Objects(case_id,"Hematoxylin_segment_std",patch_size,tmp_patch_polygon,Hematoxylin_segment_std_normalized);       
      print index2,grayscale_segment_mean_normalized,grayscale_segment_std_normalized,Hematoxylin_segment_mean_normalized,Hematoxylin_segment_std_normalized;
      if(grayscale_segment_mean_normalized>1.0 or grayscale_segment_mean_normalized<0.0):
        print "wrong";
        exit();       
      if(grayscale_segment_std_normalized>1.0 or grayscale_segment_std_normalized<0.0):
        print "wrong";
        exit();
      if(Hematoxylin_segment_mean_normalized>1.0 or Hematoxylin_segment_mean_normalized<0.0):
        print "wrong";
        exit();
      if(Hematoxylin_segment_std_normalized>1.0 or Hematoxylin_segment_std_normalized<0.0):
        print "wrong";
        exit();      
        
      Flatness_segment_mean=feature_record["Flatness_segment_mean"];             
      Flatness_segment_mean_normalized=float(Flatness_segment_mean - min_Flatness_segment_mean)/float(max_Flatness_segment_mean-min_Flatness_segment_mean);      
      Flatness_segment_std=feature_record["Flatness_segment_std"];
      Flatness_segment_std_normalized=float(Flatness_segment_std - min_Flatness_segment_std)/float(max_Flatness_segment_std-min_Flatness_segment_std);       
      Perimeter_segment_mean=feature_record["Perimeter_segment_mean"];
      Perimeter_segment_mean_normalized=float(Perimeter_segment_mean - min_Perimeter_segment_mean)/float(max_Perimeter_segment_mean-min_Perimeter_segment_mean);
      Perimeter_segment_std=feature_record["Perimeter_segment_std"];
      Perimeter_segment_std_normalized=float(Perimeter_segment_std - min_Perimeter_segment_std)/float(max_Perimeter_segment_std-min_Perimeter_segment_std);           
      save2Objects(case_id,"Flatness_segment_mean",patch_size,tmp_patch_polygon,Flatness_segment_mean_normalized); 
      save2Objects(case_id,"Flatness_segment_std",patch_size,tmp_patch_polygon,Flatness_segment_std_normalized);
      save2Objects(case_id,"Perimeter_segment_mean",patch_size,tmp_patch_polygon,Perimeter_segment_mean_normalized); 
      save2Objects(case_id,"Perimeter_segment_std",patch_size,tmp_patch_polygon,Perimeter_segment_std_normalized);      
      print index2,Flatness_segment_mean_normalized,Flatness_segment_std_normalized,Perimeter_segment_mean_normalized,Perimeter_segment_std_normalized;
      if(Flatness_segment_mean_normalized>1.0 or Flatness_segment_mean_normalized<0.0):
        print "wrong";
        exit();       
      if(Flatness_segment_std_normalized>1.0 or Flatness_segment_std_normalized<0.0):
        print "wrong";
        exit();
      if(Perimeter_segment_mean_normalized>1.0 or Perimeter_segment_mean_normalized<0.0):
        print "wrong";
        exit();
      if(Perimeter_segment_std_normalized>1.0 or Perimeter_segment_std_normalized<0.0):
        print "wrong";
        exit();       
      
      Circularity_segment_mean=feature_record["Circularity_segment_mean"];             
      Circularity_segment_mean_normalized=float(Circularity_segment_mean - min_Circularity_segment_mean)/float(max_Circularity_segment_mean-min_Circularity_segment_mean);            
      Circularity_segment_std=feature_record["Circularity_segment_std"];
      Circularity_segment_std_normalized=float(Circularity_segment_std - min_Circularity_segment_std)/float(max_Circularity_segment_std-min_Circularity_segment_std);          
      r_GradientMean_segment_mean=feature_record["r_GradientMean_segment_mean"];
      r_GradientMean_segment_mean_normalized=float(r_GradientMean_segment_mean - min_r_GradientMean_segment_mean)/float(max_r_GradientMean_segment_mean-min_r_GradientMean_segment_mean);      
      r_GradientMean_segment_std=feature_record["r_GradientMean_segment_std"];
      r_GradientMean_segment_std_normalized=float(r_GradientMean_segment_std - min_r_GradientMean_segment_std)/float(max_r_GradientMean_segment_std-min_r_GradientMean_segment_std);                 
      save2Objects(case_id,"Circularity_segment_mean",patch_size,tmp_patch_polygon,Circularity_segment_mean_normalized); 
      save2Objects(case_id,"Circularity_segment_std",patch_size,tmp_patch_polygon,Circularity_segment_std_normalized);
      save2Objects(case_id,"r_GradientMean_segment_mean",patch_size,tmp_patch_polygon,r_GradientMean_segment_mean_normalized); 
      save2Objects(case_id,"r_GradientMean_segment_std",patch_size,tmp_patch_polygon,r_GradientMean_segment_std_normalized);      
      print index2,Circularity_segment_mean_normalized,Circularity_segment_std_normalized,r_GradientMean_segment_mean_normalized,r_GradientMean_segment_std_normalized;
      if(Circularity_segment_mean_normalized>1.0 or Circularity_segment_mean_normalized<0.0):
        print "wrong";
        exit();       
      if(Circularity_segment_std_normalized>1.0 or Circularity_segment_std_normalized<0.0):
        print "wrong";
        exit();
      if(r_GradientMean_segment_mean_normalized>1.0 or r_GradientMean_segment_mean_normalized<0.0):
        print "wrong";
        exit();
      if(r_GradientMean_segment_std_normalized>1.0 or r_GradientMean_segment_std_normalized<0.0):
        print "wrong";
        exit();       
       
      b_GradientMean_segment_mean=feature_record["b_GradientMean_segment_mean"];             
      b_GradientMean_segment_mean_normalized=float(b_GradientMean_segment_mean - min_b_GradientMean_segment_mean)/float(max_b_GradientMean_segment_mean-min_b_GradientMean_segment_mean);                 
      b_GradientMean_segment_std=feature_record["b_GradientMean_segment_std"];
      b_GradientMean_segment_std_normalized=float(b_GradientMean_segment_std - min_b_GradientMean_segment_std)/float(max_b_GradientMean_segment_std-min_b_GradientMean_segment_std);                
      r_cytoIntensityMean_segment_mean=feature_record["r_cytoIntensityMean_segment_mean"];
      r_cytoIntensityMean_segment_mean_normalized=float(r_cytoIntensityMean_segment_mean - min_r_cytoIntensityMean_segment_mean)/float(max_r_cytoIntensityMean_segment_mean-min_r_cytoIntensityMean_segment_mean);          
      r_cytoIntensityMean_segment_std=feature_record["r_cytoIntensityMean_segment_std"];
      r_cytoIntensityMean_segment_std_normalized=float(r_cytoIntensityMean_segment_std - min_r_cytoIntensityMean_segment_std)/float(max_r_cytoIntensityMean_segment_std-min_r_cytoIntensityMean_segment_std); 
                          
      save2Objects(case_id,"b_GradientMean_segment_mean",patch_size,tmp_patch_polygon,b_GradientMean_segment_mean_normalized);       
      save2Objects(case_id,"b_GradientMean_segment_std",patch_size,tmp_patch_polygon,b_GradientMean_segment_std_normalized);
      save2Objects(case_id,"r_cytoIntensityMean_segment_mean",patch_size,tmp_patch_polygon,r_cytoIntensityMean_segment_mean_normalized); 
      save2Objects(case_id,"r_cytoIntensityMean_segment_std",patch_size,tmp_patch_polygon,r_cytoIntensityMean_segment_std_normalized);  
          
      print index2,b_GradientMean_segment_mean_normalized,b_GradientMean_segment_std_normalized,r_cytoIntensityMean_segment_mean_normalized,r_cytoIntensityMean_segment_std_normalized;
      if(b_GradientMean_segment_mean_normalized>1.0 or b_GradientMean_segment_mean_normalized<0.0):
        print "wrong";
        exit();       
      if(b_GradientMean_segment_std_normalized>1.0 or b_GradientMean_segment_std_normalized<0.0):
        print "wrong";
        exit();
      if(r_cytoIntensityMean_segment_mean_normalized>1.0 or r_cytoIntensityMean_segment_mean_normalized<0.0):
        print "wrong";
        exit();
      if(r_cytoIntensityMean_segment_std_normalized>1.0 or r_cytoIntensityMean_segment_std_normalized<0.0):
        print "wrong";
        exit();     
      
      b_cytoIntensityMean_segment_mean=feature_record["b_cytoIntensityMean_segment_mean"];             
      b_cytoIntensityMean_segment_mean_normalized=float(b_cytoIntensityMean_segment_mean - min_b_cytoIntensityMean_segment_mean)/float(max_b_cytoIntensityMean_segment_mean-min_b_cytoIntensityMean_segment_mean);                      
      b_cytoIntensityMean_segment_std=feature_record["b_cytoIntensityMean_segment_std"];
      b_cytoIntensityMean_segment_std_normalized=float(b_cytoIntensityMean_segment_std - min_b_cytoIntensityMean_segment_std)/float(max_b_cytoIntensityMean_segment_std-min_b_cytoIntensityMean_segment_std);      
      save2Objects(case_id,"b_cytoIntensityMean_segment_mean",patch_size,tmp_patch_polygon,b_cytoIntensityMean_segment_mean_normalized); 
      save2Objects(case_id,"b_cytoIntensityMean_segment_std",patch_size,tmp_patch_polygon,b_cytoIntensityMean_segment_std_normalized);  
      print index2,b_cytoIntensityMean_segment_mean_normalized,b_cytoIntensityMean_segment_std_normalized;
      if(b_cytoIntensityMean_segment_mean_normalized>1.0 or b_cytoIntensityMean_segment_mean_normalized<0.0):
        print "wrong";
        exit();       
      if(b_cytoIntensityMean_segment_std_normalized>1.0 or b_cytoIntensityMean_segment_std_normalized<0.0):
        print "wrong";
        exit();  
                                                     
  exit();  
 
