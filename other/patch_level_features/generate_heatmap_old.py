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
  
  patch_level_dataset = db2.patch_level_features_new;  
  
  #heatmap_type="tumor";
  heatmap_type="non_tumor";
  #heatmap_type="all";
    
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
      title="PL_percent_nuclear_material_"+heatmap_type;
      analysis_execution_id ="PL_percent_nuclear_material_"+heatmap_type;        
    elif (feature_name=="grayscale_patch_mean"):
      title="PL_grayscale_patch_mean_"+heatmap_type;
      analysis_execution_id ="PL_grayscale_patch_mean_"+heatmap_type;    
    elif (feature_name=="grayscale_patch_std"):
      title="PL_grayscale_patch_std_"+heatmap_type;
      analysis_execution_id ="PL_grayscale_patch_std_"+heatmap_type;
    elif (feature_name=="Hematoxylin_patch_mean"):
      title="PL_Hematoxylin_patch_mean_"+heatmap_type;
      analysis_execution_id ="PL_Hematoxylin_patch_mean_"+heatmap_type;   
    elif (feature_name=="Hematoxylin_patch_std"):
      title="PL_Hematoxylin_patch_std_"+heatmap_type;
      analysis_execution_id ="PL_Hematoxylin_patch_std_"+heatmap_type;      
    
    elif (feature_name=="grayscale_segment_mean"):
      title="PL_grayscale_segment_mean_"+heatmap_type;
      analysis_execution_id ="PL_grayscale_segment_mean_"+heatmap_type;    
    elif (feature_name=="grayscale_segment_std"):
      title="PL_grayscale_segment_std_"+heatmap_type;
      analysis_execution_id ="PL_grayscale_segment_std_"+heatmap_type;
    elif (feature_name=="Hematoxylin_segment_mean"):
      title="PL_Hematoxylin_segment_mean_"+heatmap_type;
      analysis_execution_id ="PL_Hematoxylin_segment_mean_"+heatmap_type;    
    elif (feature_name=="Hematoxylin_segment_std"):
      title="PL_Hematoxylin_segment_std_"+heatmap_type;
      analysis_execution_id ="PL_Hematoxylin_segment_std_"+heatmap_type;      
   
    dict_meta['color'] = 'yellow'
    dict_meta['title'] = title
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
      analysis_execution_id ="PL_percent_nuclear_material_"+heatmap_type;  
        
    elif (feature_name=="grayscale_patch_mean"):      
      analysis_execution_id ="PL_grayscale_patch_mean_"+heatmap_type;      
    elif (feature_name=="grayscale_patch_std"):      
      analysis_execution_id ="PL_grayscale_patch_std_"+heatmap_type; 
    elif (feature_name=="Hematoxylin_patch_mean"):      
      analysis_execution_id ="PL_Hematoxylin_patch_mean_"+heatmap_type;      
    elif (feature_name=="Hematoxylin_patch_std"):      
      analysis_execution_id ="PL_Hematoxylin_patch_std_"+heatmap_type;
   
    elif (feature_name=="grayscale_segment_mean"):      
      analysis_execution_id ="PL_grayscale_segment_mean_"+heatmap_type;      
    elif (feature_name=="grayscale_segment_std"):      
      analysis_execution_id ="PL_grayscale_segment_std_"+heatmap_type; 
    elif (feature_name=="Hematoxylin_segment_mean"):      
      analysis_execution_id ="PL_Hematoxylin_segment_mean_"+heatmap_type;      
    elif (feature_name=="Hematoxylin_segment_std"):      
      analysis_execution_id ="PL_Hematoxylin_segment_std_"+heatmap_type;
         
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
                       
  ######################################################################
  def removeAllHeatmaps_all(case_id):    
    metadata.remove({"image.case_id":case_id,
                     "provenance.analysis_execution_id":"PL_percent_nuclear_material_all"}); 
    metadata.remove({"image.case_id":case_id,
                     "provenance.analysis_execution_id":"PL_grayscale_patch_mean_all"});    
    metadata.remove({"image.case_id":case_id,
                     "provenance.analysis_execution_id":"PL_grayscale_patch_std_all"});
    metadata.remove({"image.case_id":case_id,
                     "provenance.analysis_execution_id":"PL_Hematoxylin_patch_mean_all"});                                                   
    metadata.remove({"image.case_id":case_id,
                     "provenance.analysis_execution_id":"PL_Hematoxylin_patch_std_all"});
    metadata.remove({"image.case_id":case_id,
                     "provenance.analysis_execution_id":"PL_grayscale_segment_mean_all"});
    metadata.remove({"image.case_id":case_id,
                     "provenance.analysis_execution_id":"PL_grayscale_segment_std_all"});
    metadata.remove({"image.case_id":case_id,
                     "provenance.analysis_execution_id":"PL_Hematoxylin_segment_mean_all"});
    metadata.remove({"image.case_id":case_id,
                     "provenance.analysis_execution_id":"PL_Hematoxylin_segment_std_all"});                     
                                                                        
    objects.remove({"provenance.image.case_id":case_id,
                     "provenance.analysis.execution_id":"PL_percent_nuclear_material_all"});                       
    objects.remove({"provenance.image.case_id":case_id,
                     "provenance.analysis.execution_id":"PL_grayscale_patch_mean_all"});
    objects.remove({"provenance.image.case_id":case_id,
                     "provenance.analysis.execution_id":"PL_grayscale_patch_std_all"});
    objects.remove({"provenance.image.case_id":case_id,
                     "provenance.analysis.execution_id":"PL_Hematoxylin_patch_mean_all"});                       
    objects.remove({"provenance.image.case_id":case_id,
                     "provenance.analysis.execution_id":"PL_Hematoxylin_patch_std_all"});
    objects.remove({"provenance.image.case_id":case_id,
                     "provenance.analysis.execution_id":"PL_grayscale_segment_mean_all"});
    objects.remove({"provenance.image.case_id":case_id,
                     "provenance.analysis.execution_id":"PL_grayscale_segment_std_all"});                       
    objects.remove({"provenance.image.case_id":case_id,
                     "provenance.analysis.execution_id":"PL_Hematoxylin_segment_mean_all"});
    objects.remove({"provenance.image.case_id":case_id,
                     "provenance.analysis.execution_id":"PL_Hematoxylin_segment_std_all"});    
                                       
  ######################################################################
                                                                     
  print '--- process image_list  ---- ';   
  for item in image_list:  
    case_id=item[0];
    user=item[1];
    
    #removeAllHeatmaps_tumor(case_id);    
    #removeAllHeatmaps_non_tumor(case_id);
    
    save2Meta(case_id,"percent_nuclear_material");    
    save2Meta(case_id,"grayscale_patch_mean");
    save2Meta(case_id,"grayscale_patch_std");
    save2Meta(case_id,"Hematoxylin_patch_mean");
    save2Meta(case_id,"Hematoxylin_patch_std");    
    save2Meta(case_id,"grayscale_segment_mean");
    save2Meta(case_id,"grayscale_segment_std");
    save2Meta(case_id,"Hematoxylin_segment_mean");
    save2Meta(case_id,"Hematoxylin_segment_std");   
    
    min_grayscale_patch_mean=0.0;
    max_grayscale_patch_mean=0.0;
    min_grayscale_patch_std=0.0;
    max_grayscale_patch_std=0.0;
    min_Hematoxylin_patch_mean=0.0;
    max_Hematoxylin_patch_mean=0.0;
    min_Hematoxylin_patch_std=0.0;
    max_Hematoxylin_patch_std=0.0;    
    
    index=0;
    for feature_record in patch_level_dataset.find({"case_id":case_id,
                                                     "user":user,
                                                     "tumorFlag":heatmap_type,
                                                     "percent_nuclear_material": { "$gte": 0.0 }}):       
      grayscale_patch_mean=feature_record["grayscale_patch_mean"];
      grayscale_patch_std=feature_record["grayscale_patch_std"];
      Hematoxylin_patch_mean=feature_record["Hematoxylin_patch_mean"];
      Hematoxylin_patch_std=feature_record["Hematoxylin_patch_std"];      
      
      if(index ==0):
        min_grayscale_patch_mean = grayscale_patch_mean; 
        max_grayscale_patch_mean = grayscale_patch_mean; 
      else:
        if (grayscale_patch_mean < min_grayscale_patch_mean ):
          min_grayscale_patch_mean = grayscale_patch_mean;
        if (grayscale_patch_mean > max_grayscale_patch_mean ):
          max_grayscale_patch_mean = grayscale_patch_mean;  
          
      if(index ==0):
        min_grayscale_patch_std = grayscale_patch_std; 
        max_grayscale_patch_std = grayscale_patch_std; 
      else:
        if (grayscale_patch_std < min_grayscale_patch_std ):
          min_grayscale_patch_std = grayscale_patch_std;
        if (grayscale_patch_std > max_grayscale_patch_std ):
          max_grayscale_patch_std = grayscale_patch_std;
      
      if(index ==0):
        min_Hematoxylin_patch_mean = Hematoxylin_patch_mean; 
        max_Hematoxylin_patch_mean = Hematoxylin_patch_mean; 
      else:
        if (Hematoxylin_patch_mean < min_Hematoxylin_patch_mean ):
          min_Hematoxylin_patch_mean = Hematoxylin_patch_mean;
        if (Hematoxylin_patch_mean > max_Hematoxylin_patch_mean ):
          max_Hematoxylin_patch_mean = Hematoxylin_patch_mean;  
          
      if(index ==0):
        min_Hematoxylin_patch_std = Hematoxylin_patch_std; 
        max_Hematoxylin_patch_std = Hematoxylin_patch_std; 
      else:
        if (Hematoxylin_patch_std < min_Hematoxylin_patch_std ):
          min_Hematoxylin_patch_std = Hematoxylin_patch_std;
        if (Hematoxylin_patch_std > max_Hematoxylin_patch_std ):
          max_Hematoxylin_patch_std = Hematoxylin_patch_std;                      
      index+=1;
      
    index2=0;
    for feature_record in patch_level_dataset.find({"case_id":case_id,
                                                     "user":user,
                                                     "tumorFlag":heatmap_type,
                                                     "percent_nuclear_material": { "$gte": 0.0 }}):      
      image_width=feature_record["image_width"];
      image_height=feature_record["image_height"];
      patch_min_x_pixel=feature_record["patch_min_x_pixel"];
      patch_min_y_pixel=feature_record["patch_min_y_pixel"];
      patch_size=feature_record["patch_size"];
      patch_polygon_area=feature_record["patch_polygon_area"];
      #nucleus_area=feature_record["nucleus_area"];
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
      
      grayscale_patch_10th_percentile=feature_record["grayscale_patch_10th_percentile"];
      grayscale_patch_25th_percentile=feature_record["grayscale_patch_25th_percentile"];
      grayscale_patch_50th_percentile=feature_record["grayscale_patch_50th_percentile"];
      grayscale_patch_75th_percentile=feature_record["grayscale_patch_75th_percentile"];
      grayscale_patch_90th_percentile=feature_record["grayscale_patch_90th_percentile"];
      Hematoxylin_patch_10th_percentile=feature_record["Hematoxylin_patch_10th_percentile"];
      Hematoxylin_patch_25th_percentile=feature_record["Hematoxylin_patch_25th_percentile"];
      Hematoxylin_patch_50th_percentile=feature_record["Hematoxylin_patch_50th_percentile"];
      Hematoxylin_patch_75th_percentile=feature_record["Hematoxylin_patch_75th_percentile"];
      Hematoxylin_patch_90th_percentile=feature_record["Hematoxylin_patch_90th_percentile"];
      segment_10th_percentile_grayscale_intensity=feature_record["segment_10th_percentile_grayscale_intensity"];
      segment_25th_percentile_grayscale_intensity=feature_record["segment_25th_percentile_grayscale_intensity"];
      segment_50th_percentile_grayscale_intensity=feature_record["segment_50th_percentile_grayscale_intensity"];
      segment_75th_percentile_grayscale_intensity=feature_record["segment_75th_percentile_grayscale_intensity"];
      segment_90th_percentile_grayscale_intensity=feature_record["segment_90th_percentile_grayscale_intensity"];
      segment_10th_percentile_hematoxylin_intensity=feature_record["segment_10th_percentile_hematoxylin_intensity"];
      segment_25th_percentile_hematoxylin_intensity=feature_record["segment_25th_percentile_hematoxylin_intensity"];
      segment_50th_percentile_hematoxylin_intensity=feature_record["segment_50th_percentile_hematoxylin_intensity"]; 
      segment_75th_percentile_hematoxylin_intensity=feature_record["segment_75th_percentile_hematoxylin_intensity"];
      segment_90th_percentile_hematoxylin_intensity=feature_record["segment_90th_percentile_hematoxylin_intensity"];        
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
      index2+=1;
      print index2,grayscale_patch_std_normalized; 
      if(grayscale_patch_std_normalized>1.0 or grayscale_patch_std_normalized<0.0):
        print "wrong";
        exit();       
        
    
    index1=0;
    for feature_record in patch_level_dataset.find({"case_id":case_id,
                                                     "user":user,
                                                     "tumorFlag":heatmap_type,
                                                     "grayscale_segment_mean": { "$ne": "n/a" }}):  
      grayscale_segment_mean=feature_record["grayscale_segment_mean"];
      grayscale_segment_std=feature_record["grayscale_segment_std"];
      Hematoxylin_segment_mean=feature_record["Hematoxylin_segment_mean"];
      Hematoxylin_segment_std=feature_record["Hematoxylin_segment_std"]; 
                                                         
      if(index1 ==0):
        min_grayscale_segment_mean = grayscale_segment_mean; 
        max_grayscale_segment_mean = grayscale_segment_mean; 
      else:
        if (grayscale_segment_mean < min_grayscale_segment_mean ):
          min_grayscale_segment_mean = grayscale_segment_mean;
        if (grayscale_segment_mean > max_grayscale_segment_mean ):
          max_grayscale_segment_mean = grayscale_segment_mean;  
          
      if(index1 ==0):
        min_grayscale_segment_std = grayscale_segment_std; 
        max_grayscale_segment_std = grayscale_segment_std; 
      else:
        if (grayscale_segment_std < min_grayscale_segment_std ):
          min_grayscale_segment_std = grayscale_segment_std;
        if (grayscale_segment_std > max_grayscale_segment_std ):
          max_grayscale_segment_std = grayscale_segment_std;
      
      if(index1 ==0):
        min_Hematoxylin_segment_mean = Hematoxylin_segment_mean; 
        max_Hematoxylin_segment_mean = Hematoxylin_segment_mean; 
      else:
        if (Hematoxylin_segment_mean < min_Hematoxylin_segment_mean ):
          min_Hematoxylin_segment_mean = Hematoxylin_segment_mean;
        if (Hematoxylin_segment_mean > max_Hematoxylin_segment_mean ):
          max_Hematoxylin_segment_mean = Hematoxylin_segment_mean;  
          
      if(index1 ==0):
        min_Hematoxylin_segment_std = Hematoxylin_segment_std; 
        max_Hematoxylin_segment_std = Hematoxylin_segment_std; 
      else:
        if (Hematoxylin_segment_std < min_Hematoxylin_segment_std ):
          min_Hematoxylin_segment_std = Hematoxylin_segment_std;
        if (Hematoxylin_segment_std > max_Hematoxylin_segment_std ):
          max_Hematoxylin_segment_std = Hematoxylin_segment_std; 
      index1+=1;                                                        
    print min_grayscale_segment_mean, min_grayscale_segment_std,min_Hematoxylin_segment_mean,min_Hematoxylin_segment_std;      
    
          
    index3=0;
    for feature_record in patch_level_dataset.find({"case_id":case_id,
                                                     "user":user,
                                                     "tumorFlag":heatmap_type,
                                                     "grayscale_segment_mean": { "$ne": "n/a" }}):      
      image_width=feature_record["image_width"];
      image_height=feature_record["image_height"];
      patch_min_x_pixel=feature_record["patch_min_x_pixel"];
      patch_min_y_pixel=feature_record["patch_min_y_pixel"];
      patch_size=feature_record["patch_size"];
      patch_polygon_area=feature_record["patch_polygon_area"];
      #nucleus_area=feature_record["nucleus_area"];
      percent_nuclear_material=feature_record["percent_nuclear_material"];
      percent_nuclear_material_normalized=percent_nuclear_material*100;         
      
      grayscale_segment_mean=feature_record["grayscale_segment_mean"];             
      grayscale_segment_mean_normalized=float(grayscale_segment_mean - min_grayscale_segment_mean)/float(max_grayscale_segment_mean-min_grayscale_segment_mean);      
      grayscale_segment_std=feature_record["grayscale_segment_std"];
      grayscale_segment_std_normalized=float(grayscale_segment_std - min_grayscale_segment_std)/float(max_grayscale_segment_std-min_grayscale_segment_std); 
      
      Hematoxylin_segment_mean=feature_record["Hematoxylin_segment_mean"];
      Hematoxylin_segment_mean_normalized=float(Hematoxylin_segment_mean - min_Hematoxylin_segment_mean)/float(max_Hematoxylin_segment_mean-min_Hematoxylin_segment_mean);
      Hematoxylin_segment_std=feature_record["Hematoxylin_segment_std"];
      Hematoxylin_segment_std_normalized=float(Hematoxylin_segment_std - min_Hematoxylin_segment_std)/float(max_Hematoxylin_segment_std-min_Hematoxylin_segment_std);         
      
      x1=float(patch_min_x_pixel)/float(image_width);
      y1=float(patch_min_y_pixel)/float(image_height);
      x2=float(patch_min_x_pixel+patch_size)/float(image_width);
      y2=float(patch_min_y_pixel+patch_size)/float(image_height);
      tmp_patch_polygon=[[x1,y1],[x2,y1],[x2,y2],[x1,y2],[x1,y1]];      
          
      save2Objects(case_id,"grayscale_segment_mean",patch_size,tmp_patch_polygon,grayscale_segment_mean_normalized); 
      save2Objects(case_id,"grayscale_segment_std",patch_size,tmp_patch_polygon,grayscale_segment_std_normalized);
      save2Objects(case_id,"Hematoxylin_segment_mean",patch_size,tmp_patch_polygon,Hematoxylin_segment_mean_normalized); 
      save2Objects(case_id,"Hematoxylin_segment_std",patch_size,tmp_patch_polygon,Hematoxylin_segment_std_normalized);        
      
      index3+=1;
      print index3;
      #exit();                  
  exit();  
 
