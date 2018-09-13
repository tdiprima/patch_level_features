from shapely.geometry import LineString
from shapely.geometry.polygon import LinearRing
from shapely.geometry import Polygon
from shapely.geometry import MultiPolygon
from shapely.affinity import affine_transform
from shapely.validation import explain_validity 
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
from datetime import datetime
import random
import concurrent.futures 
import logging
    
    
if __name__ == '__main__':
  if len(sys.argv)<2:
    print "usage:python run_jobs.py case_id user";
    exit(); 
    
  LOG_FILENAME = 'readme.log'  
  logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG) 
   
  csv.field_size_limit(sys.maxsize); 
  max_workers=16;  
  
  case_id = sys.argv[1]; 
  user= sys.argv[2] ;
  
  image_list=[];  
  tmp_array=[[],[]];
  tmp_array[0]=case_id;   
  tmp_array[1]=user;
  image_list.append(tmp_array);   
  print image_list;  
  
  my_home="/data1/bwang"  
  
  remote_dataset_folder="nfs004:/data/shared/bwang/composite_dataset";   
  local_dataset_folder = os.path.join(my_home, 'dataset');  
  if not os.path.exists(local_dataset_folder):
    print '%s folder do not exist, then create it.' % local_dataset_folder;
    os.makedirs(local_dataset_folder); 
  
  remote_image_folder="nfs001:/data/shared/tcga_analysis/seer_data/images";      
  local_image_folder = os.path.join(my_home, 'img'); 
  if not os.path.exists(local_image_folder):
    print '%s folder do not exist, then create it.' % local_image_folder;
    os.makedirs(local_image_folder);
  
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
    
  collection_saved= db2.patch_level_features_run3; 
  
  image_width=0;
  image_height=0; 
  mpp_x=0.0;
  mpp_y=0.0;   
  tolerance=1.0; 
 
  x, y = np.meshgrid(np.arange(patch_size), np.arange(patch_size)) # make a canvas with coordinates
  x, y = x.flatten(), y.flatten();
  points = np.vstack((x,y)).T ;
  
  #######################################
  def findPrefixList(case_id):    
    prefix_list=[];  
    input_file="case_id_prefix.txt"
    prefix_file = os.path.join(my_home, input_file); 
    with open(prefix_file, 'r') as my_file:
      reader = csv.reader(my_file,delimiter=',')
      my_list = list(reader);
      for each_row in my_list:      
        file_path=each_row[0];#path        
        if file_path.find(case_id) <> -1:#find it!
          perfix_path = each_row[0];           
          position_1=perfix_path.rfind('/')+1;
          position_2=len(perfix_path);
          prefix=perfix_path[position_1:position_2];         
          prefix_list.append(prefix)           
    return  prefix_list;  
  ###############################################
  
  
  ###############################################
  def read_csv_data_file(file_path,data_file):    
    obj_list=[];
    csv_file = os.path.join(file_path, data_file);
    with open(csv_file, 'rb') as csv_read:
      reader = csv.reader(csv_read);
      headers = reader.next();          
      polygon_index= headers.index('Polygon');   
      Flatness_index= headers.index('Flatness');
      Perimeter_index= headers.index('Perimeter');
      Circularity_index= headers.index('Circularity');
      r_GradientMean_index= headers.index('r_GradientMean');
      b_GradientMean_index= headers.index('b_GradientMean');
      r_cytoIntensityMean_index= headers.index('r_cytoIntensityMean');
      b_cytoIntensityMean_index= headers.index('b_cytoIntensityMean');  
      Elongation_index= headers.index('Elongation');
                      
      for row in reader: 
        patch_item=[[],[],[],[],[],[],[],[],[],[]];           
        current_polygon=row[polygon_index] ;        
        new_polygon=[];            
        tmp_str=str(current_polygon);            
        tmp_str=tmp_str.replace('[','');
        tmp_str=tmp_str.replace(']','');
        split_str=tmp_str.split(':');
        for i in range(0, len(split_str)-1, 2):
          point=[float(split_str[i])/float(image_width),float(split_str[i+1])/float(image_height)];
          new_polygon.append(point);              
        tmp_poly=[tuple(i) for i in new_polygon];
        computer_polygon0 = Polygon(tmp_poly);
        computer_polygon = computer_polygon0.buffer(0);         
        patch_item[0]=computer_polygon;
        patch_item[1]=row[Flatness_index] ;
        patch_item[2]=row[Perimeter_index] ;
        patch_item[3]=row[Circularity_index] ;
        patch_item[4]=row[r_GradientMean_index] ;
        patch_item[5]=row[b_GradientMean_index] ;
        patch_item[6]=row[r_cytoIntensityMean_index] ;
        patch_item[7]=row[b_cytoIntensityMean_index] ;  
        patch_item[8]=row[Elongation_index] ;
        patch_item[9]=computer_polygon0;      
        obj_list.append(patch_item);    
    return  obj_list;             
  ###############################################
  
  ###############################################
  def getImageMetaData(local_img_folder,prefix_list):
    for prefix in prefix_list:
      detail_local_folder  = os.path.join(local_img_folder, prefix);      
      if os.path.isdir(detail_local_folder) and len(os.listdir(detail_local_folder)) > 0:                            
         json_filename_list = [f for f in os.listdir(detail_local_folder) if f.endswith('.json')] ;                       
         for json_filename in json_filename_list:             
           with open(os.path.join(detail_local_folder, json_filename)) as f:
             data = json.load(f);             
             image_width=data["image_width"];
             image_height=data["image_height"];            
             return image_width,image_height;  
  ###############################################  
  
  ###############################################
  def getTileMetaData(tile_min_point,local_img_folder,prefix_list):
    x=tile_min_point[0];
    y=tile_min_point[1];
    tmp_string="_x"+str(x)+"_y" + str(y);      
    for prefix in prefix_list:
      detail_local_folder  = os.path.join(local_img_folder, prefix);      
      if os.path.isdir(detail_local_folder) and len(os.listdir(detail_local_folder)) > 0:                            
         json_filename_list = [f for f in os.listdir(detail_local_folder) if f.endswith('.json')] ;                       
         for json_filename in json_filename_list:   
           if (json_filename.find(tmp_string) <> -1):  #find it!        
             with open(os.path.join(detail_local_folder, json_filename)) as f:
               data = json.load(f);                  
               tile_width=data["tile_width"];
               tile_height=data["tile_height"];                      
               return tile_width,tile_height;  
  ############################################### 
   
  #######################################################
  def findUniqueTileList(local_img_folder,prefix_list):
    tile_min_point_list=[] 
    for prefix in prefix_list:
      detail_local_folder  = os.path.join(local_img_folder, prefix);      
      if os.path.isdir(detail_local_folder) and len(os.listdir(detail_local_folder)) > 0:                            
         json_filename_list = [f for f in os.listdir(detail_local_folder) if f.endswith('.json')] ;                      
         for json_filename in json_filename_list:                        
           with open(os.path.join(detail_local_folder, json_filename)) as f:
             data = json.load(f);            
             tile_minx=data["tile_minx"];
             tile_miny=data["tile_miny"];                         
             point=[tile_minx,tile_miny];
             tile_min_point_list.append(point);     
    tmp_set = set(map(tuple,tile_min_point_list))
    unique_tile_min_point_list = map(list,tmp_set)
    return unique_tile_min_point_list;
  #######################################################    
  
  ###############################################
  def getCompositeDatasetExecutionID(case_id):
    execution_id="";
    for record in metadata2.find({"image.case_id":case_id,                 
				                          "provenance.analysis_execution_id":{'$regex' : 'composite_dataset', '$options' : 'i'}}).limit(1): 
      execution_id=record["provenance"]["analysis_execution_id"];
      break;
    return execution_id;    
  #################################################  
  
  #######################################################
  def getPolygonCountFromDB(case_id,comp_execution_id,polygon0):    
    tmp_poly=[tuple(i1) for i1 in polygon0];
    tmp_polygon = Polygon(tmp_poly);
    patch_polygon_tmp = tmp_polygon.buffer(0); 
    x1=polygon0[0][0]
    y1=polygon0[0][1] 
    x2=polygon0[2][0]
    y2=polygon0[2][1]     
    patch_width_unit=float(x2-x1)/float(image_width); 
    patch_height_unit=float(y2-y1)/float(image_height); 
    x1_new=float(x1-(patch_width_unit*tolerance));
    y1_new=float(y1-(patch_height_unit*tolerance));
    x2_new=float(x2+(patch_width_unit*tolerance));
    y2_new=float(y2+(patch_height_unit*tolerance));  
    #deal with out of boundry 
    if x1_new>1.0:
      x1_new=1.0;
    if x1_new<0.0:
      x1_new=0.0; 
    if x2_new>1.0:
      x2_new=1.0;            
    if x2_new<0.0:
      x2_new=0.0;            
    if y1_new>1.0:
      y1_new=1.0;
    if y1_new<0.0:
      y1_new=0.0; 
    if y2_new>1.0:
      y2_new=1.0;
    if y2_new<0.0:
      y2_new=0.0;  
    counter=0;  
    area_tmp=0.0;                                                     
    for nuclues_polygon in objects2.find({"provenance.image.case_id":case_id,
                                          "provenance.analysis.execution_id":comp_execution_id,                                                                                                   
                                          "x" : { '$gte':x1_new, '$lte':x2_new},
                                          "y" : { '$gte':y1_new, '$lte':y2_new} },
                                          {"geometry":1,"properties":1,"_id":0}):
      nuclear_polygon=nuclues_polygon["geometry"]["coordinates"][0]; 
      #exclude those nuclear objects, which are out of patch boundry
      take_this_polygon=False;
      tmp_poly=[tuple(i2) for i2 in nuclear_polygon];
      computer_polygon_obj = Polygon(tmp_poly);
      computer_polygon_obj2 = computer_polygon_obj.buffer(0);
      if (computer_polygon_obj2.within(patch_polygon_tmp)):
        take_this_polygon=True;
      if (computer_polygon_obj2.intersects(patch_polygon_tmp)):
        take_this_polygon=True;
      if take_this_polygon:                                  
        counter+=1; 
        area_tmp=area_tmp+computer_polygon_obj2.area;
        #print computer_polygon_obj2.area,computer_polygon_obj2.bounds;
    return counter,area_tmp;    
  #######################################################    
  
  #############################################
  def findTumor_NonTumorRegions(case_id,user):
    execution_id=user+"_Tumor_Region";
    execution_id2=user+"_Non_Tumor_Region";
    
    #handle only tumor region overlap
    humanMarkupList_tumor=[];
    tmp_tumor_markup_list=[];
    
    for humarkup in objects.find({"provenance.image.case_id":case_id,
                                  "provenance.analysis.execution_id":execution_id},
                                 {"geometry":1,"_id":1}):                         
      tmp_tumor_markup_list.append(humarkup);    
              
    index_intersected=[];                                
    for index1 in range(0, len(tmp_tumor_markup_list)):  
      if index1 in index_intersected :#skip polygon,which is been merged to another one
        continue;
      tmp_tumor_markup1=tmp_tumor_markup_list[index1];                               
      humarkup_polygon_tmp1=tmp_tumor_markup1["geometry"]["coordinates"][0];             
      tmp_polygon=[tuple(i1) for i1 in humarkup_polygon_tmp1];
      tmp_polygon1 = Polygon(tmp_polygon);    
      humarkup_polygon1 = tmp_polygon1.buffer(0);      
      humarkup_polygon_bound1= humarkup_polygon1.bounds;      
      is_within=False;
      is_intersect=False;
      for index2 in range(0, len(tmp_tumor_markup_list)):  
        tmp_tumor_markup2=tmp_tumor_markup_list[index2];                               
        humarkup_polygon_tmp2=tmp_tumor_markup2["geometry"]["coordinates"][0];             
        tmp_polygon2=[tuple(i2) for i2 in humarkup_polygon_tmp2];
        tmp_polygon22 = Polygon(tmp_polygon2);        
        humarkup_polygon2 = tmp_polygon22.buffer(0); 
        if (index1 <> index2):
          if (humarkup_polygon1.within(humarkup_polygon2)):    
            is_within=True;            
            break;              
          if (humarkup_polygon1.intersects(humarkup_polygon2)):
            humarkup_polygon1=humarkup_polygon1.union(humarkup_polygon2); 
            is_intersect=True;
            index_intersected.append(index2);                
      if(not is_within and not is_intersect):
        humanMarkupList_tumor.append(humarkup_polygon1);          
      if(is_within):
        continue;         
      if(is_intersect):          
        humanMarkupList_tumor.append(humarkup_polygon1);            
        
    #handle only non tumor region overlap
    humanMarkupList_non_tumor=[];
    tmp_non_tumor_markup_list=[];
    for humarkup in objects.find({"provenance.image.case_id":case_id,
                                  "provenance.analysis.execution_id":execution_id2},
                                 {"geometry":1,"_id":0}):
      tmp_non_tumor_markup_list.append(humarkup);     
        
    index_intersected=[];                                
    for index1 in range(0, len(tmp_non_tumor_markup_list)):  
      if index1 in index_intersected :#skip polygon,which is been merged to another one
        continue;
      tmp_tumor_markup1=tmp_non_tumor_markup_list[index1];                               
      humarkup_polygon_tmp1=tmp_tumor_markup1["geometry"]["coordinates"][0];             
      tmp_polygon=[tuple(i1) for i1 in humarkup_polygon_tmp1];
      tmp_polygon1 = Polygon(tmp_polygon);      
      humarkup_polygon1 = tmp_polygon1.convex_hull;
      humarkup_polygon1 = humarkup_polygon1.buffer(0);
      humarkup_polygon_bound1= humarkup_polygon1.bounds;
      is_within=False;
      is_intersect=False;
      for index2 in range(0, len(tmp_non_tumor_markup_list)):  
        tmp_tumor_markup2=tmp_non_tumor_markup_list[index2];                               
        humarkup_polygon_tmp2=tmp_tumor_markup2["geometry"]["coordinates"][0];             
        tmp_polygon2=[tuple(i2) for i2 in humarkup_polygon_tmp2];
        tmp_polygon22 = Polygon(tmp_polygon2);
        humarkup_polygon2=tmp_polygon22.convex_hull;
        humarkup_polygon2 = humarkup_polygon2.buffer(0);
        if (index1 <> index2):
          if (humarkup_polygon1.within(humarkup_polygon2)):    
            is_within=True;            
            break;              
          if (humarkup_polygon1.intersects(humarkup_polygon2)):
            humarkup_polygon1=humarkup_polygon1.union(humarkup_polygon2); 
            is_intersect=True;
            index_intersected.append(index2);                
      if(not is_within and not is_intersect):
        humanMarkupList_non_tumor.append(humarkup_polygon1);          
      if(is_within):
        continue;         
      if(is_intersect):          
        humanMarkupList_non_tumor.append(humarkup_polygon1);
        
    #handle tumor and non tumor region cross overlap
    for index1,tumor_region in enumerate(humanMarkupList_tumor):
      for index2,non_tumor_region in enumerate(humanMarkupList_non_tumor):
        if (tumor_region.within(non_tumor_region)): 
          ext_polygon_intersect_points =list(zip(*non_tumor_region.exterior.coords.xy));   
          int_polygon_intersect_points =list(zip(*tumor_region.exterior.coords.xy)); 
          newPoly = Polygon(ext_polygon_intersect_points,[int_polygon_intersect_points]);
          humanMarkupList_non_tumor[index2]=newPoly;#add a hole to this polygon
        elif (non_tumor_region.within(tumor_region)): 
          ext_polygon_intersect_points =list(zip(*tumor_region.exterior.coords.xy));   
          int_polygon_intersect_points =list(zip(*non_tumor_region.exterior.coords.xy)); 
          newPoly = Polygon(ext_polygon_intersect_points,[int_polygon_intersect_points]);
          humanMarkupList_tumor[index1]=newPoly;#add a hole to this polygon   
    
    return  humanMarkupList_tumor,humanMarkupList_non_tumor;     
  ################################################
  
  #######################################
  def findImagePath(case_id):
    image_path="";  
    input_file="image_path.txt"
    image_path_file = os.path.join(my_home, input_file); 
    with open(image_path_file, 'r') as my_file:
      reader = csv.reader(my_file,delimiter=',')
      my_list = list(reader);
      for each_row in my_list:      
        file_path=each_row[0];#path
        if file_path.find(case_id) <> -1:#find it!
          image_path = each_row[0]; 
          image_path = image_path.replace('./','');       
          break
    return  image_path;  
  ###############################################
  
  ##################################
  def getMatrixValue(poly_in,patch_min_x_pixel,patch_min_y_pixel):          
    tmp_polygon =[];            
    for ii in range (0,len(poly_in)):   
      x0=poly_in[ii][0];
      y0=poly_in[ii][1];                 
      x01=(x0*image_width)- patch_min_x_pixel;
      y01=(y0*image_height)- patch_min_y_pixel;
      x01=int(round(x01)); 
      y01=int(round(y01));                
      point=[x01,y01];
      tmp_polygon.append(point);           
    if (len(tmp_polygon) >0):   
      path = Path(tmp_polygon)            
      grid = path.contains_points(points);
      return True,grid;
    else:
      return False, "";          
  ##################################################  
  
  ##################################################
  def removeOverlapPolygon(nuclear_item_list):
    overlapPolygonIndx=999999;
    nuclues_polygon_count=len(nuclear_item_list);
    for i2 in range(0,nuclues_polygon_count-1):
      for j2 in range(1,nuclues_polygon_count): 
        if (i2<>j2):
          polygon1=nuclear_item_list[i2][0];
          polygon2=nuclear_item_list[j2][0];
          if (polygon1.within(polygon2)):
            print "polygon " + str(i2)+" is within polygon " + str(j2);
            overlapPolygonIndx=j2;
            del nuclear_item_list[overlapPolygonIndx];
            return nuclear_item_list;
          if (polygon2.within(polygon1)):
            print "polygon " + str(j2)+" is within polygon " + str(i2);
            overlapPolygonIndx=i2;
            del nuclear_item_list[overlapPolygonIndx];
            return nuclear_item_list;                               
     
    return nuclear_item_list;     
  ##################################################
  
  #########################################################
  def saveFeatures2MongoDB(case_id,image_width,image_height,mpp_x,mpp_y,user,title_index,patch_min_x_pixel,patch_min_y_pixel,patch_size,patch_polygon_area,patch_area_seleted_percentage,tumorFlag,nucleus_area,percent_nuclear_material,grayscale_patch_mean,grayscale_patch_std,Hematoxylin_patch_mean,Hematoxylin_patch_std,grayscale_segment_mean,grayscale_segment_std,Hematoxylin_segment_mean,Hematoxylin_segment_std,Flatness_segment_mean,Flatness_segment_std,Perimeter_segment_mean,Perimeter_segment_std,Circularity_segment_mean,Circularity_segment_std,r_GradientMean_segment_mean,r_GradientMean_segment_std,b_GradientMean_segment_mean,b_GradientMean_segment_std,r_cytoIntensityMean_segment_mean,r_cytoIntensityMean_segment_std,b_cytoIntensityMean_segment_mean,b_cytoIntensityMean_segment_std,Elongation_segment_mean,Elongation_segment_std):
    patch_feature_data = collections.OrderedDict();
    patch_feature_data['case_id'] = case_id;
    patch_feature_data['image_width'] = image_width;
    patch_feature_data['image_height'] = image_height;  
    patch_feature_data['mpp_x'] = mpp_x;
    patch_feature_data['mpp_y'] = mpp_y;      
    patch_feature_data['user'] = user;
    patch_feature_data['title_index'] = title_index;    
    patch_feature_data['patch_min_x_pixel'] =patch_min_x_pixel;
    patch_feature_data['patch_min_y_pixel'] = patch_min_y_pixel;
    patch_feature_data['patch_size'] = patch_size;    
    patch_feature_data['patch_polygon_area'] = patch_polygon_area;      
    patch_feature_data['patch_area_seleted_percentage'] = patch_area_seleted_percentage; 
    patch_feature_data['tumorFlag'] = tumorFlag;  
    patch_feature_data['nucleus_area'] = nucleus_area;  
    patch_feature_data['percent_nuclear_material'] = percent_nuclear_material;
    patch_feature_data['grayscale_patch_mean'] = grayscale_patch_mean;
    patch_feature_data['grayscale_patch_std'] = grayscale_patch_std;
    patch_feature_data['Hematoxylin_patch_mean'] = Hematoxylin_patch_mean;
    patch_feature_data['Hematoxylin_patch_std'] = Hematoxylin_patch_std;
    patch_feature_data['grayscale_segment_mean'] = grayscale_segment_mean;
    patch_feature_data['grayscale_segment_std'] = grayscale_segment_std;
    patch_feature_data['Hematoxylin_segment_mean'] = Hematoxylin_segment_mean;
    patch_feature_data['Hematoxylin_segment_std'] = Hematoxylin_segment_std;       
    patch_feature_data['Flatness_segment_mean'] = Flatness_segment_mean;  
    patch_feature_data['Flatness_segment_std'] = Flatness_segment_std;
    patch_feature_data['Perimeter_segment_mean'] = Perimeter_segment_mean;
    patch_feature_data['Perimeter_segment_std'] = Perimeter_segment_std;
    patch_feature_data['Circularity_segment_mean'] = Circularity_segment_mean;    
    patch_feature_data['Circularity_segment_std'] = Circularity_segment_std;  
    patch_feature_data['r_GradientMean_segment_mean'] = r_GradientMean_segment_mean;
    patch_feature_data['r_GradientMean_segment_std'] = r_GradientMean_segment_std;
    patch_feature_data['b_GradientMean_segment_mean'] = b_GradientMean_segment_mean;
    patch_feature_data['b_GradientMean_segment_std'] = b_GradientMean_segment_std;    
    patch_feature_data['r_cytoIntensityMean_segment_mean'] = r_cytoIntensityMean_segment_mean;  
    patch_feature_data['r_cytoIntensityMean_segment_std'] = r_cytoIntensityMean_segment_std;
    patch_feature_data['b_cytoIntensityMean_segment_mean'] = b_cytoIntensityMean_segment_mean;
    patch_feature_data['b_cytoIntensityMean_segment_std'] = b_cytoIntensityMean_segment_std; 
    patch_feature_data['Elongation_segment_mean'] = Elongation_segment_mean;
    patch_feature_data['Elongation_segment_std'] = Elongation_segment_std;  
    patch_feature_data['datetime'] = datetime.now();               
    collection_saved.insert_one(patch_feature_data);         
  ######################################################################  
  
  ######################################################################
  def process_one_patch(case_id,user,tile_index,patch_polygon_area0,patch_polygon_area1,patch_polygon_area2,image_width,image_height,mpp_x,mpp_y,patch_polygon_original,patchHumanMarkupRelation_tumor,patchHumanMarkupRelation_nontumor,patch_humanmarkup_intersect_polygon_tumor,patch_humanmarkup_intersect_polygon_nontumor,nuclues_item_list):    
    patch_min_x_pixel =int(patch_polygon_original[0][0]*image_width);
    patch_min_y_pixel =int(patch_polygon_original[0][1]*image_height);
    patch_max_x_pixel =int(patch_polygon_original[2][0]*image_width);
    patch_max_y_pixel =int(patch_polygon_original[2][1]*image_height);
    x10=patch_polygon_original[0][0];
    y10=patch_polygon_original[0][1];
    x20=patch_polygon_original[2][0];
    y20=patch_polygon_original[2][1];        
    patch_width_unit=float(patch_size)/float(image_width); 
    patch_height_unit=float(patch_size)/float(image_height);
    
    try:
      patch_img= img.read_region((patch_min_x_pixel, patch_min_y_pixel), 0, (patch_size, patch_size));
    except openslide.OpenSlideError as detail:
      print 'Handling run-time error:', detail  
      exit();
    except Exception as e: 
      print(e);
      exit();
      
    tmp_poly=[tuple(i1) for i1 in patch_polygon_original];
    tmp_polygon = Polygon(tmp_poly);
    patch_polygon = tmp_polygon.buffer(0);    
          
    grayscale_img = patch_img.convert('L');
    rgb_img = patch_img.convert('RGB');        
    grayscale_img_matrix=np.array(grayscale_img);  
    rgb_img_matrix=np.array(rgb_img);         
    grayscale_patch_mean=np.mean(grayscale_img_matrix);
    grayscale_patch_std=np.std(grayscale_img_matrix);                
    hed_title_img = separate_stains(rgb_img_matrix, hed_from_rgb);    
    max1=np.max(hed_title_img);
    min1=np.min(hed_title_img);
    Hematoxylin_img_matrix=hed_title_img [:,:,0];
    Hematoxylin_img_matrix =((Hematoxylin_img_matrix -min1)*255/(max1-min1)).astype(np.uint8);    
    Hematoxylin_patch_mean=np.mean(Hematoxylin_img_matrix);
    Hematoxylin_patch_std=np.std(Hematoxylin_img_matrix);              
          
    nucleus_area=0.0;#tumor patch area
    nucleus_area2=0.0;#non_tumor patch area
    factor=float(image_width)*float(image_height)*mpp_x*mpp_y;
    #print "\n";
    #print " ---- tile_index,patch_min_x_pixel,patch_min_y_pixel,patch_polygon_area0,patch_polygon_area1,patch_polygon_area2,len(nuclues_item_list) ---";
    #print tile_index,patch_min_x_pixel,patch_min_y_pixel,patch_polygon_area0,patch_polygon_area1,patch_polygon_area2,len(nuclues_item_list);
    
    #object level features selected
    Flatness_list=[];
    Perimeter_list=[];
    Circularity_list=[];
    r_GradientMean_list=[];
    b_GradientMean_list=[];
    r_cytoIntensityMean_list=[];
    b_cytoIntensityMean_list=[];
    Elongation_list=[];
    
    segment_img=[];
    segment_img_hematoxylin=[];         
    initial_grid=np.full((patch_size*patch_size), False);        
    findPixelWithinPolygon=False;     
    special_case1="";
    tumorFlag="";
    patchHumanMarkupRelation="";
    patch_humanmarkup_intersect_polygon = Polygon([(0, 0), (1, 1), (1, 0)]);
    
    if(patchHumanMarkupRelation_tumor=="intersect" and patchHumanMarkupRelation_nontumor=="intersect"):
      special_case1="both";
    elif (patchHumanMarkupRelation_tumor=="intersect"):
      special_case1="tumor";  
      tumorFlag="tumor";  
      patchHumanMarkupRelation="intersect";
      patch_humanmarkup_intersect_polygon=patch_humanmarkup_intersect_polygon_tumor;
    elif (patchHumanMarkupRelation_nontumor=="intersect"):
      special_case1="nontumor";
      tumorFlag="non_tumor";
      patchHumanMarkupRelation="intersect";
      patch_humanmarkup_intersect_polygon=patch_humanmarkup_intersect_polygon_nontumor;
    elif (patchHumanMarkupRelation_tumor=="within"):
      special_case1="tumor";  
      tumorFlag="tumor"; 
      patchHumanMarkupRelation="within";
      patch_humanmarkup_intersect_polygon=patch_humanmarkup_intersect_polygon_tumor;
    elif (patchHumanMarkupRelation_nontumor=="within"):
      special_case1="nontumor";
      tumorFlag="non_tumor";
      patchHumanMarkupRelation="within";
      patch_humanmarkup_intersect_polygon=patch_humanmarkup_intersect_polygon_nontumor;    
   
    record_count =len(nuclues_item_list);
    if (record_count>0 and special_case1<>"both"):                                                                         
      for item in nuclues_item_list: 
        computer_polygon=item[0]; 
        Flatness_value=float(item[1]);
        Perimeter_value=float(item[2]);
        Circularity_value=float(item[3]);
        r_GradientMean_value=float(item[4]);
        b_GradientMean_value=float(item[5]);
        r_cytoIntensityMean_value=float(item[6]);
        b_cytoIntensityMean_value=float(item[7]); 
        Elongation_value=float(item[8]); 
        computer_polygon_points =list(zip(*computer_polygon.exterior.coords.xy));
        
        polygon_area= computer_polygon.area;                          
        special_case2=""; 
        
        #only calculate features within/intersect tumor or non tumor region 
        if (patchHumanMarkupRelation=="within"):
           special_case2="within";           
        elif (patchHumanMarkupRelation=="intersect"):              
          if(computer_polygon.within(patch_humanmarkup_intersect_polygon)):                
            special_case2="within";
          elif(computer_polygon.intersects(patch_humanmarkup_intersect_polygon)):               
            special_case2="intersects";
          else:                
            special_case2="disjoin";   
                                    
          if (special_case2=="disjoin"):
            continue;#skip this one and move to another computer polygon              
                       
        if (special_case2=="within" and computer_polygon.within(patch_polygon)):#within/within            
          nucleus_area=nucleus_area+polygon_area; 
          #print "within/within";
          #print  polygon_area;   
          Flatness_list.append(Flatness_value);
          Perimeter_list.append(Perimeter_value);
          Circularity_list.append(Circularity_value);
          r_GradientMean_list.append(r_GradientMean_value);
          b_GradientMean_list.append(b_GradientMean_value);
          r_cytoIntensityMean_list.append(r_cytoIntensityMean_value);
          b_cytoIntensityMean_list.append(b_cytoIntensityMean_value); 
          Elongation_list.append(Elongation_value);
          has_value,one_polygon_mask=getMatrixValue(computer_polygon_points,patch_min_x_pixel,patch_min_y_pixel); 
          if(has_value):
            #print "initial_grid.shape,one_polygon_mask.shape";
            #print initial_grid.shape,one_polygon_mask.shape;
            initial_grid = initial_grid | one_polygon_mask; 
            findPixelWithinPolygon=True;                                        
        elif (special_case2=="within" and computer_polygon.intersects(patch_polygon)):#within/intersects 
          Flatness_list.append(Flatness_value);
          Perimeter_list.append(Perimeter_value);
          Circularity_list.append(Circularity_value);
          r_GradientMean_list.append(r_GradientMean_value);
          b_GradientMean_list.append(b_GradientMean_value);
          r_cytoIntensityMean_list.append(r_cytoIntensityMean_value);
          b_cytoIntensityMean_list.append(b_cytoIntensityMean_value);
          Elongation_list.append(Elongation_value);
          polygon_intersect=computer_polygon.intersection(patch_polygon);
          if polygon_intersect.is_empty:
            continue;
          tmp_area=polygon_intersect.area;
          nucleus_area=nucleus_area+tmp_area; 
          #print "within/intersects";
          #print tmp_area;
          #print patch_polygon.bounds;          
          #print computer_polygon.geom_type;
          #print computer_polygon.bounds; 
          #print polygon_intersect.geom_type;
          #print polygon_intersect.bounds;
          
          another_area=0.0;                                    
          if polygon_intersect.geom_type == 'MultiPolygon':                                 
            for p in polygon_intersect:
              another_area=another_area+p.area;
              #print "--p.area--";
              #print p.area;
              polygon_intersect_points =list(zip(*p.exterior.coords.xy));                                    
              has_value,one_polygon_mask=getMatrixValue(polygon_intersect_points,patch_min_x_pixel,patch_min_y_pixel);  
              if(has_value):
                initial_grid = initial_grid | one_polygon_mask; 
                findPixelWithinPolygon=True;  
            #print "another_area";
            #print another_area;                                                                   
          elif polygon_intersect.geom_type == 'Polygon':               
            polygon_intersect_points =list(zip(*polygon_intersect.exterior.coords.xy));                                
            has_value,one_polygon_mask=getMatrixValue(polygon_intersect_points,patch_min_x_pixel,patch_min_y_pixel);  
            if(has_value):
              initial_grid = initial_grid | one_polygon_mask; 
              findPixelWithinPolygon=True;             
          else:               
            print "patch indexes %d Shape is not a polygon!!!" %tile_index; 
            print polygon_intersect.geom_type;
            #print polygon_intersect;                    
        elif (special_case2=="intersects" and computer_polygon.within(patch_polygon)):#intersects/within
          Flatness_list.append(Flatness_value);
          Perimeter_list.append(Perimeter_value);
          Circularity_list.append(Circularity_value);
          r_GradientMean_list.append(r_GradientMean_value);
          b_GradientMean_list.append(b_GradientMean_value);
          r_cytoIntensityMean_list.append(r_cytoIntensityMean_value);
          b_cytoIntensityMean_list.append(b_cytoIntensityMean_value);
          Elongation_list.append(Elongation_value);
          starttime=time.time();
          polygon_intersect=computer_polygon.intersection(patch_humanmarkup_intersect_polygon); 
          if polygon_intersect.is_empty:
            continue; 
          tmp_area=polygon_intersect.area;
          nucleus_area=nucleus_area+tmp_area; 
          #print "intersects/within";
          #print  tmp_area;                         
          if polygon_intersect.geom_type == 'MultiPolygon':                                 
            for p in polygon_intersect:
              polygon_intersect_points =list(zip(*p.exterior.coords.xy));                               
              has_value,one_polygon_mask=getMatrixValue(polygon_intersect_points,patch_min_x_pixel,patch_min_y_pixel);   
              if(has_value):
                initial_grid = initial_grid | one_polygon_mask; 
                findPixelWithinPolygon=True;                                                                
          elif polygon_intersect.geom_type == 'Polygon':                
            polygon_intersect_points =list(zip(*polygon_intersect.exterior.coords.xy));                              
            has_value,one_polygon_mask=getMatrixValue(polygon_intersect_points,patch_min_x_pixel,patch_min_y_pixel);
            if(has_value):
              initial_grid = initial_grid | one_polygon_mask;   
              findPixelWithinPolygon=True;              
          else:               
            print "patch indexes %d Shape is not a polygon!!!" %tile_index; 
            print polygon_intersect.geom_type;
            #print polygon_intersect;                   
        elif (special_case2=="intersects" and computer_polygon.intersects(patch_polygon)):#intersects/intersects
          Flatness_list.append(Flatness_value);
          Perimeter_list.append(Perimeter_value);
          Circularity_list.append(Circularity_value);
          r_GradientMean_list.append(r_GradientMean_value);
          b_GradientMean_list.append(b_GradientMean_value);
          r_cytoIntensityMean_list.append(r_cytoIntensityMean_value);
          b_cytoIntensityMean_list.append(b_cytoIntensityMean_value);
          Elongation_list.append(Elongation_value);
          starttime=time.time();
          polygon_intersect=computer_polygon.intersection(patch_polygon);
          if polygon_intersect.is_empty:
            continue;
          polygon_intersect=polygon_intersect.intersection(patch_humanmarkup_intersect_polygon); 
          if polygon_intersect.is_empty:
            continue;              
          tmp_area=polygon_intersect.area;
          nucleus_area=nucleus_area+tmp_area; 
          #print "intersects/intersects";
          #print  tmp_area;                          
          if polygon_intersect.geom_type == 'MultiPolygon':                                 
            for p in polygon_intersect:
              polygon_intersect_points =list(zip(*p.exterior.coords.xy));                                   
              has_value,one_polygon_mask=getMatrixValue(polygon_intersect_points,patch_min_x_pixel,patch_min_y_pixel);
              if(has_value):
                initial_grid = initial_grid | one_polygon_mask; 
                findPixelWithinPolygon=True;                                                                    
          elif polygon_intersect.geom_type == 'Polygon':               
            polygon_intersect_points =list(zip(*polygon_intersect.exterior.coords.xy));                                   
            has_value,one_polygon_mask=getMatrixValue(polygon_intersect_points,patch_min_x_pixel,patch_min_y_pixel);
            if(has_value):
              initial_grid = initial_grid | one_polygon_mask;  
              findPixelWithinPolygon=True;               
          else:               
            print "patch indexes %d Shape is not a polygon!!!" %tile_index;  
            print polygon_intersect.geom_type;
            #print polygon_intersect;
    
    if(special_case1<>"both"):        
      if(findPixelWithinPolygon):          
        mask = initial_grid.reshape(patch_size,patch_size);             
        for index1,row in enumerate(mask):
          for index2,pixel in enumerate(row):
            if (pixel):#this pixel is inside of segmented unclei polygon                     
              segment_img.append(grayscale_img_matrix[index1][index2]);
              segment_img_hematoxylin.append(Hematoxylin_img_matrix[index1][index2]); 
                  
      if(tumorFlag=="non_tumor"):
        patch_polygon_area=patch_polygon_area2;
        percent_nuclear_material =float((nucleus_area/patch_polygon_area)*100); 
      elif (tumorFlag=="tumor"):
        patch_polygon_area=patch_polygon_area1;
        percent_nuclear_material =float((nucleus_area/patch_polygon_area)*100);
      else:
        patch_polygon_area=patch_polygon_area0;
        percent_nuclear_material =float((nucleus_area/patch_polygon_area)*100); 
        
      patch_area_seleted_percentage=float((patch_polygon_area/patch_polygon_area0)*100);
      #print  "patch_polygon_area,nucleus_area";
      #print  patch_polygon_area,nucleus_area;
      #print "\n";
          
      if (len(segment_img)>0):          
        segment_mean_grayscale_intensity= np.mean(segment_img);
        segment_std_grayscale_intensity= np.std(segment_img);         
        segment_mean_hematoxylin_intensity= np.mean(segment_img_hematoxylin);
        segment_std_hematoxylin_intensity= np.std(segment_img_hematoxylin);                          
      else:
        segment_mean_grayscale_intensity="n/a";
        segment_std_grayscale_intensity="n/a";
        segment_mean_hematoxylin_intensity="n/a";
        segment_std_hematoxylin_intensity="n/a";            
      
      if (len(Flatness_list)>0):                
        Flatness_segment_mean= np.mean(Flatness_list);
        Flatness_segment_std= np.std(Flatness_list); 
      else:
        Flatness_segment_mean="n/a";
        Flatness_segment_std="n/a";
              
      if (len(Perimeter_list)>0):
        Perimeter_segment_mean= np.mean(Perimeter_list);
        Perimeter_segment_std= np.std(Perimeter_list);  
      else:
        Perimeter_segment_mean="n/a";
        Perimeter_segment_std="n/a";
            
      if (len(Circularity_list)>0):
        Circularity_segment_mean= np.mean(Circularity_list);
        Circularity_segment_std= np.std(Circularity_list);  
      else:
        Circularity_segment_mean="n/a";
        Circularity_segment_std="n/a";
              
      if (len(r_GradientMean_list)>0):
        r_GradientMean_segment_mean= np.mean(r_GradientMean_list);
        r_GradientMean_segment_std= np.std(r_GradientMean_list);
      else:
        r_GradientMean_segment_mean="n/a";  
        r_GradientMean_segment_std="n/a";
        
      if (len(b_GradientMean_list)>0):
        b_GradientMean_segment_mean= np.mean(b_GradientMean_list);
        b_GradientMean_segment_std= np.std(b_GradientMean_list);
      else:
        b_GradientMean_segment_mean="n/a";
        b_GradientMean_segment_std="n/a";
          
      if (len(r_cytoIntensityMean_list)>0):
        r_cytoIntensityMean_segment_mean= np.mean(r_cytoIntensityMean_list);
        r_cytoIntensityMean_segment_std= np.std(r_cytoIntensityMean_list);
      else:
        r_cytoIntensityMean_segment_mean="n/a";
        r_cytoIntensityMean_segment_std="n/a";
          
      if (len(b_cytoIntensityMean_list)>0):
        b_cytoIntensityMean_segment_mean= np.mean(b_cytoIntensityMean_list);
        b_cytoIntensityMean_segment_std= np.std(b_cytoIntensityMean_list);
      else:
        b_cytoIntensityMean_segment_mean="n/a";
        b_cytoIntensityMean_segment_std="n/a"; 
        
      if (len(Elongation_list)>0):
        Elongation_segment_mean= np.mean(Elongation_list);
        Elongation_segment_std= np.std(Elongation_list);
      else:
        Elongation_segment_mean="n/a";
        Elongation_segment_std="n/a";                  
      
      #convert area to physical area image_width,image_height,mpp-x,mpp-p      
      patch_polygon_area_new=patch_polygon_area*factor;
      nucleus_area_new = nucleus_area*factor;
      print case_id,image_width,image_height,user,tile_index,patch_min_x_pixel,patch_min_y_pixel,patch_size,patch_polygon_area_new,tumorFlag,nucleus_area_new,percent_nuclear_material,grayscale_patch_mean,grayscale_patch_std,Hematoxylin_patch_mean,Hematoxylin_patch_std,segment_mean_grayscale_intensity,segment_std_grayscale_intensity,segment_mean_hematoxylin_intensity,segment_std_hematoxylin_intensity,Flatness_segment_mean,Flatness_segment_std,Perimeter_segment_mean,Perimeter_segment_std,Circularity_segment_mean,Circularity_segment_std,r_GradientMean_segment_mean,r_GradientMean_segment_std,b_GradientMean_segment_mean,b_GradientMean_segment_std,r_cytoIntensityMean_segment_mean,r_cytoIntensityMean_segment_std,b_cytoIntensityMean_segment_mean,b_cytoIntensityMean_segment_std,Elongation_segment_mean,Elongation_segment_std;
      print "\n";      
      saveFeatures2MongoDB(case_id,image_width,image_height,mpp_x,mpp_y,user,tile_index,patch_min_x_pixel,patch_min_y_pixel,patch_size,patch_polygon_area_new,patch_area_seleted_percentage,tumorFlag,nucleus_area_new,percent_nuclear_material,grayscale_patch_mean,grayscale_patch_std,Hematoxylin_patch_mean,Hematoxylin_patch_std,segment_mean_grayscale_intensity,segment_std_grayscale_intensity,segment_mean_hematoxylin_intensity,segment_std_hematoxylin_intensity,Flatness_segment_mean,Flatness_segment_std,Perimeter_segment_mean,Perimeter_segment_std,Circularity_segment_mean,Circularity_segment_std,r_GradientMean_segment_mean,r_GradientMean_segment_std,b_GradientMean_segment_mean,b_GradientMean_segment_std,r_cytoIntensityMean_segment_mean,r_cytoIntensityMean_segment_std,b_cytoIntensityMean_segment_mean,b_cytoIntensityMean_segment_std,Elongation_segment_mean,Elongation_segment_std);     
    
    #case of both
    patchHumanMarkupRelation=patchHumanMarkupRelation_tumor;
    patch_humanmarkup_intersect_polygon= patch_humanmarkup_intersect_polygon_tumor;
    tumorFlag="tumor";
    if (record_count>0 and special_case1=="both"):                                                                      
      for item in nuclues_item_list:                                            
        computer_polygon=item[0]; 
        Flatness_value=float(item[1]);
        Perimeter_value=float(item[2]);
        Circularity_value=float(item[3]);
        r_GradientMean_value=float(item[4]);
        b_GradientMean_value=float(item[5]);
        r_cytoIntensityMean_value=float(item[6]);
        b_cytoIntensityMean_value=float(item[7]);
        Elongation_value=float(item[8]);
        polygon_area= computer_polygon.area;                          
        special_case2="";       
        
        #only calculate features within/intersect tumor or non tumor region 
        if (patchHumanMarkupRelation=="within"):
           special_case2="within";           
        elif (patchHumanMarkupRelation=="intersect"):              
          if(computer_polygon.within(patch_humanmarkup_intersect_polygon)):                
            special_case2="within";
          elif(computer_polygon.intersects(patch_humanmarkup_intersect_polygon)):               
            special_case2="intersects";
          else:                
            special_case2="disjoin";   
                                    
          if (special_case2=="disjoin"):
            continue;#skip this one and move to another computer polygon              
                       
        if (special_case2=="within" and computer_polygon.within(patch_polygon)):#within/within 
          Flatness_list.append(Flatness_value);
          Perimeter_list.append(Perimeter_value);
          Circularity_list.append(Circularity_value);
          r_GradientMean_list.append(r_GradientMean_value);
          b_GradientMean_list.append(b_GradientMean_value);
          r_cytoIntensityMean_list.append(r_cytoIntensityMean_value);
          b_cytoIntensityMean_list.append(b_cytoIntensityMean_value);
          Elongation_list.append(Elongation_value);
          nucleus_area=nucleus_area+polygon_area;                                         
          has_value,one_polygon_mask=getMatrixValue(polygon,patch_min_x_pixel,patch_min_y_pixel); 
          if(has_value):
            initial_grid = initial_grid | one_polygon_mask; 
            findPixelWithinPolygon=True;                                        
        elif (special_case2=="within" and computer_polygon.intersects(patch_polygon)):#within/intersects   
          Flatness_list.append(Flatness_value);
          Perimeter_list.append(Perimeter_value);
          Circularity_list.append(Circularity_value);
          r_GradientMean_list.append(r_GradientMean_value);
          b_GradientMean_list.append(b_GradientMean_value);
          r_cytoIntensityMean_list.append(r_cytoIntensityMean_value);
          b_cytoIntensityMean_list.append(b_cytoIntensityMean_value);
          Elongation_list.append(Elongation_value);
          polygon_intersect=computer_polygon.intersection(patch_polygon);
          if polygon_intersect.is_empty:
            continue;
          tmp_area=polygon_intersect.area;
          nucleus_area=nucleus_area+tmp_area;                            
          if polygon_intersect.geom_type == 'MultiPolygon':                                 
            for p in polygon_intersect:
              polygon_intersect_points =list(zip(*p.exterior.coords.xy));                                    
              has_value,one_polygon_mask=getMatrixValue(polygon_intersect_points,patch_min_x_pixel,patch_min_y_pixel);  
              if(has_value):
                initial_grid = initial_grid | one_polygon_mask; 
                findPixelWithinPolygon=True;                                                                
          elif polygon_intersect.geom_type == 'Polygon':               
            polygon_intersect_points =list(zip(*polygon_intersect.exterior.coords.xy));                                
            has_value,one_polygon_mask=getMatrixValue(polygon_intersect_points,patch_min_x_pixel,patch_min_y_pixel);  
            if(has_value):
              initial_grid = initial_grid | one_polygon_mask; 
              findPixelWithinPolygon=True;             
          else:               
            print "patch indexes %d Shape is not a polygon!!!" %tile_index; 
            print polygon_intersect.geom_type;
            #print polygon_intersect;                    
        elif (special_case2=="intersects" and computer_polygon.within(patch_polygon)):#intersects/within
          Flatness_list.append(Flatness_value);
          Perimeter_list.append(Perimeter_value);
          Circularity_list.append(Circularity_value);
          r_GradientMean_list.append(r_GradientMean_value);
          b_GradientMean_list.append(b_GradientMean_value);
          r_cytoIntensityMean_list.append(r_cytoIntensityMean_value);
          b_cytoIntensityMean_list.append(b_cytoIntensityMean_value);
          Elongation_list.append(Elongation_value);
          starttime=time.time();
          polygon_intersect=computer_polygon.intersection(patch_humanmarkup_intersect_polygon); 
          if polygon_intersect.is_empty:
            continue; 
          tmp_area=polygon_intersect.area;
          nucleus_area=nucleus_area+tmp_area;                          
          if polygon_intersect.geom_type == 'MultiPolygon':                                 
            for p in polygon_intersect:
              polygon_intersect_points =list(zip(*p.exterior.coords.xy));                               
              has_value,one_polygon_mask=getMatrixValue(polygon_intersect_points,patch_min_x_pixel,patch_min_y_pixel);   
              if(has_value):
                initial_grid = initial_grid | one_polygon_mask; 
                findPixelWithinPolygon=True;                                                                
          elif polygon_intersect.geom_type == 'Polygon':                
            polygon_intersect_points =list(zip(*polygon_intersect.exterior.coords.xy));                              
            has_value,one_polygon_mask=getMatrixValue(polygon_intersect_points,patch_min_x_pixel,patch_min_y_pixel);
            if(has_value):
              initial_grid = initial_grid | one_polygon_mask;   
              findPixelWithinPolygon=True;              
          else:               
            print "patch indexes %d Shape is not a polygon!!!" %tile_index; 
            print polygon_intersect.geom_type;
            #print polygon_intersect;                   
        elif (special_case2=="intersects" and computer_polygon.intersects(patch_polygon)):#intersects/intersects
          Flatness_list.append(Flatness_value);
          Perimeter_list.append(Perimeter_value);
          Circularity_list.append(Circularity_value);
          r_GradientMean_list.append(r_GradientMean_value);
          b_GradientMean_list.append(b_GradientMean_value);
          r_cytoIntensityMean_list.append(r_cytoIntensityMean_value);
          b_cytoIntensityMean_list.append(b_cytoIntensityMean_value);
          Elongation_list.append(Elongation_value);
          starttime=time.time();
          polygon_intersect=computer_polygon.intersection(patch_polygon);
          if polygon_intersect.is_empty:
            continue;
          polygon_intersect=polygon_intersect.intersection(patch_humanmarkup_intersect_polygon); 
          if polygon_intersect.is_empty:
            continue;              
          tmp_area=polygon_intersect.area;
          nucleus_area=nucleus_area+tmp_area;                           
          if polygon_intersect.geom_type == 'MultiPolygon':                                 
            for p in polygon_intersect:
              polygon_intersect_points =list(zip(*p.exterior.coords.xy));                                   
              has_value,one_polygon_mask=getMatrixValue(polygon_intersect_points,patch_min_x_pixel,patch_min_y_pixel);
              if(has_value):
                initial_grid = initial_grid | one_polygon_mask; 
                findPixelWithinPolygon=True;                                                                    
          elif polygon_intersect.geom_type == 'Polygon':               
            polygon_intersect_points =list(zip(*polygon_intersect.exterior.coords.xy));                                   
            has_value,one_polygon_mask=getMatrixValue(polygon_intersect_points,patch_min_x_pixel,patch_min_y_pixel);
            if(has_value):
              initial_grid = initial_grid | one_polygon_mask;  
              findPixelWithinPolygon=True;               
          else:               
            print "patch indexes %d Shape is not a polygon!!!" %tile_index;  
            print polygon_intersect.geom_type;
            #print polygon_intersect;
    
    if(special_case1=="both" and tumorFlag=="tumor"):        
      if(findPixelWithinPolygon):          
        mask = initial_grid.reshape(patch_size,patch_size);             
        for index1,row in enumerate(mask):
          for index2,pixel in enumerate(row):
            if (pixel):#this pixel is inside of segmented unclei polygon                     
              segment_img.append(grayscale_img_matrix[index1][index2]);
              segment_img_hematoxylin.append(Hematoxylin_img_matrix[index1][index2]);     
               
      percent_nuclear_material =float((nucleus_area/patch_polygon_area1)*100); 
              
      if (len(segment_img)>0):          
        segment_mean_grayscale_intensity= np.mean(segment_img);
        segment_std_grayscale_intensity= np.std(segment_img);         
        segment_mean_hematoxylin_intensity= np.mean(segment_img_hematoxylin);
        segment_std_hematoxylin_intensity= np.std(segment_img_hematoxylin);                             
      else:
        segment_mean_grayscale_intensity="n/a";
        segment_std_grayscale_intensity="n/a";
        segment_mean_hematoxylin_intensity="n/a";
        segment_std_hematoxylin_intensity="n/a";       
      
      if (len(Flatness_list)>0):
        Flatness_segment_mean= np.mean(Flatness_list);
        Flatness_segment_std= np.std(Flatness_list); 
      else:
        Flatness_segment_mean="n/a";
        Flatness_segment_std="n/a";
              
      if (len(Perimeter_list)>0):
        Perimeter_segment_mean= np.mean(Perimeter_list);
        Perimeter_segment_std= np.std(Perimeter_list);  
      else:
        Perimeter_segment_mean="n/a";
        Perimeter_segment_std="n/a";
            
      if (len(Circularity_list)>0):
        Circularity_segment_mean= np.mean(Circularity_list);
        Circularity_segment_std= np.std(Circularity_list);  
      else:
        Circularity_segment_mean="n/a";
        Circularity_segment_std="n/a";
              
      if (len(r_GradientMean_list)>0):
        r_GradientMean_segment_mean= np.mean(r_GradientMean_list);
        r_GradientMean_segment_std= np.std(r_GradientMean_list);
      else:
        r_GradientMean_segment_mean="n/a";  
        r_GradientMean_segment_std="n/a";
        
      if (len(b_GradientMean_list)>0):
        b_GradientMean_segment_mean= np.mean(b_GradientMean_list);
        b_GradientMean_segment_std= np.std(b_GradientMean_list);
      else:
        b_GradientMean_segment_mean="n/a";
        b_GradientMean_segment_std="n/a";
          
      if (len(r_cytoIntensityMean_list)>0):
        r_cytoIntensityMean_segment_mean= np.mean(r_cytoIntensityMean_list);
        r_cytoIntensityMean_segment_std= np.std(r_cytoIntensityMean_list);
      else:
        r_cytoIntensityMean_segment_mean="n/a";
        r_cytoIntensityMean_segment_std="n/a";
          
      if (len(b_cytoIntensityMean_list)>0):
        b_cytoIntensityMean_segment_mean= np.mean(b_cytoIntensityMean_list);
        b_cytoIntensityMean_segment_std= np.std(b_cytoIntensityMean_list);
      else:
        b_cytoIntensityMean_segment_mean="n/a";
        b_cytoIntensityMean_segment_std="n/a";  
        
      if (len(Elongation_list)>0):
        Elongation_segment_mean= np.mean(Elongation_list);
        Elongation_segment_std= np.std(Elongation_list);
      else:
        Elongation_segment_mean="n/a";
        Elongation_segment_std="n/a";                
      
      #convert area to physical area image_width,image_height,mpp-x,mpp-p      
      patch_polygon_area_new=patch_polygon_area1*factor;
      nucleus_area_new = nucleus_area*factor;       
      patch_area_seleted_percentage=float((patch_polygon_area1/patch_polygon_area0)*100);
      
      print case_id,image_width,image_height,user,title_index,patch_min_x_pixel,patch_min_y_pixel,patch_size,patch_polygon_area_new,tumorFlag,nucleus_area_new,percent_nuclear_material,grayscale_patch_mean,grayscale_patch_std,Hematoxylin_patch_mean,Hematoxylin_patch_std,segment_mean_grayscale_intensity,segment_std_grayscale_intensity,segment_mean_hematoxylin_intensity,segment_std_hematoxylin_intensity,Flatness_segment_mean,Flatness_segment_std,Perimeter_segment_mean,Perimeter_segment_std,Circularity_segment_mean,Circularity_segment_std,r_GradientMean_segment_mean,r_GradientMean_segment_std,b_GradientMean_segment_mean,b_GradientMean_segment_std,r_cytoIntensityMean_segment_mean,r_cytoIntensityMean_segment_std,b_cytoIntensityMean_segment_mean,b_cytoIntensityMean_segment_std,Elongation_segment_mean,Elongation_segment_std;  
      print "\n";   
      saveFeatures2MongoDB(case_id,image_width,image_height,mpp_x,mpp_y,user,title_index,patch_min_x_pixel,patch_min_y_pixel,patch_size,patch_polygon_area_new,patch_area_seleted_percentage,tumorFlag,nucleus_area_new,percent_nuclear_material,grayscale_patch_mean,grayscale_patch_std,Hematoxylin_patch_mean,Hematoxylin_patch_std,segment_mean_grayscale_intensity,segment_std_grayscale_intensity,segment_mean_hematoxylin_intensity,segment_std_hematoxylin_intensity,Flatness_segment_mean,Flatness_segment_std,Perimeter_segment_mean,Perimeter_segment_std,Circularity_segment_mean,Circularity_segment_std,r_GradientMean_segment_mean,r_GradientMean_segment_std,b_GradientMean_segment_mean,b_GradientMean_segment_std,r_cytoIntensityMean_segment_mean,r_cytoIntensityMean_segment_std,b_cytoIntensityMean_segment_mean,b_cytoIntensityMean_segment_std,Elongation_segment_mean,Elongation_segment_std);     
    
    #case of both   
    patchHumanMarkupRelation=patchHumanMarkupRelation_nontumor;
    patch_humanmarkup_intersect_polygon= patch_humanmarkup_intersect_polygon_nontumor;
    tumorFlag="non_tumor";      
    if (record_count>0 and special_case1=="both"):                                                                      
      for item in nuclues_item_list:                                            
        computer_polygon=item[0]; 
        Flatness_value=float(item[1]);
        Perimeter_value=float(item[2]);
        Circularity_value=float(item[3]);
        r_GradientMean_value=float(item[4]);
        b_GradientMean_value=float(item[5]);
        r_cytoIntensityMean_value=float(item[6]);
        b_cytoIntensityMean_value=float(item[7]);
        Elongation_value=float(item[8]);
        polygon_area= computer_polygon.area;                          
        special_case2=""; 
               
        #only calculate features within/intersect tumor or non tumor region 
        if (patchHumanMarkupRelation=="within"):
           special_case2="within";           
        elif (patchHumanMarkupRelation=="intersect"):              
          if(computer_polygon.within(patch_humanmarkup_intersect_polygon)):                
            special_case2="within";
          elif(computer_polygon.intersects(patch_humanmarkup_intersect_polygon)):               
            special_case2="intersects";
          else:                
            special_case2="disjoin";   
                                    
          if (special_case2=="disjoin"):
            continue;#skip this one and move to another computer polygon              
                       
        if (special_case2=="within" and computer_polygon.within(patch_polygon)):#within/within   
          Flatness_list.append(Flatness_value);
          Perimeter_list.append(Perimeter_value);
          Circularity_list.append(Circularity_value);
          r_GradientMean_list.append(r_GradientMean_value);
          b_GradientMean_list.append(b_GradientMean_value);
          r_cytoIntensityMean_list.append(r_cytoIntensityMean_value);
          b_cytoIntensityMean_list.append(b_cytoIntensityMean_value);
          Elongation_list.append(Elongation_value);
          nucleus_area=nucleus_area+polygon_area;                                         
          has_value,one_polygon_mask=getMatrixValue(polygon,patch_min_x_pixel,patch_min_y_pixel); 
          if(has_value):
            initial_grid = initial_grid | one_polygon_mask; 
            findPixelWithinPolygon=True;                                        
        elif (special_case2=="within" and computer_polygon.intersects(patch_polygon)):#within/intersects  
          Flatness_list.append(Flatness_value);
          Perimeter_list.append(Perimeter_value);
          Circularity_list.append(Circularity_value);
          r_GradientMean_list.append(r_GradientMean_value);
          b_GradientMean_list.append(b_GradientMean_value);
          r_cytoIntensityMean_list.append(r_cytoIntensityMean_value);
          b_cytoIntensityMean_list.append(b_cytoIntensityMean_value);
          Elongation_list.append(Elongation_value);
          polygon_intersect=computer_polygon.intersection(patch_polygon);
          if polygon_intersect.is_empty:
            continue;
          tmp_area=polygon_intersect.area;
          nucleus_area=nucleus_area+tmp_area;                            
          if polygon_intersect.geom_type == 'MultiPolygon':                                 
            for p in polygon_intersect:
              polygon_intersect_points =list(zip(*p.exterior.coords.xy));                                    
              has_value,one_polygon_mask=getMatrixValue(polygon_intersect_points,patch_min_x_pixel,patch_min_y_pixel);  
              if(has_value):
                initial_grid = initial_grid | one_polygon_mask; 
                findPixelWithinPolygon=True;                                                                
          elif polygon_intersect.geom_type == 'Polygon':               
            polygon_intersect_points =list(zip(*polygon_intersect.exterior.coords.xy));                                
            has_value,one_polygon_mask=getMatrixValue(polygon_intersect_points,patch_min_x_pixel,patch_min_y_pixel);  
            if(has_value):
              initial_grid = initial_grid | one_polygon_mask; 
              findPixelWithinPolygon=True;             
          else:               
            print "patch indexes %d Shape is not a polygon!!!" %tile_index; 
            print polygon_intersect.geom_type;
            #print polygon_intersect;                    
        elif (special_case2=="intersects" and computer_polygon.within(patch_polygon)):#intersects/within
          Flatness_list.append(Flatness_value);
          Perimeter_list.append(Perimeter_value);
          Circularity_list.append(Circularity_value);
          r_GradientMean_list.append(r_GradientMean_value);
          b_GradientMean_list.append(b_GradientMean_value);
          r_cytoIntensityMean_list.append(r_cytoIntensityMean_value);
          b_cytoIntensityMean_list.append(b_cytoIntensityMean_value);
          Elongation_list.append(Elongation_value);
          starttime=time.time();
          polygon_intersect=computer_polygon.intersection(patch_humanmarkup_intersect_polygon); 
          if polygon_intersect.is_empty:
            continue; 
          tmp_area=polygon_intersect.area;
          nucleus_area=nucleus_area+tmp_area;                          
          if polygon_intersect.geom_type == 'MultiPolygon':                                 
            for p in polygon_intersect:
              polygon_intersect_points =list(zip(*p.exterior.coords.xy));                               
              has_value,one_polygon_mask=getMatrixValue(polygon_intersect_points,patch_min_x_pixel,patch_min_y_pixel);   
              if(has_value):
                initial_grid = initial_grid | one_polygon_mask; 
                findPixelWithinPolygon=True;                                                                
          elif polygon_intersect.geom_type == 'Polygon':                
            polygon_intersect_points =list(zip(*polygon_intersect.exterior.coords.xy));                              
            has_value,one_polygon_mask=getMatrixValue(polygon_intersect_points,patch_min_x_pixel,patch_min_y_pixel);
            if(has_value):
              initial_grid = initial_grid | one_polygon_mask;   
              findPixelWithinPolygon=True;              
          else:               
            print "patch indexes %d Shape is not a polygon!!!" %tile_index; 
            print polygon_intersect.geom_type;
            #print polygon_intersect;                   
        elif (special_case2=="intersects" and computer_polygon.intersects(patch_polygon)):#intersects/intersects
          Flatness_list.append(Flatness_value);
          Perimeter_list.append(Perimeter_value);
          Circularity_list.append(Circularity_value);
          r_GradientMean_list.append(r_GradientMean_value);
          b_GradientMean_list.append(b_GradientMean_value);
          r_cytoIntensityMean_list.append(r_cytoIntensityMean_value);
          b_cytoIntensityMean_list.append(b_cytoIntensityMean_value);
          Elongation_list.append(Elongation_value);
          starttime=time.time();
          polygon_intersect=computer_polygon.intersection(patch_polygon);
          if polygon_intersect.is_empty:
            continue;
          polygon_intersect=polygon_intersect.intersection(patch_humanmarkup_intersect_polygon); 
          if polygon_intersect.is_empty:
            continue;              
          tmp_area=polygon_intersect.area;
          nucleus_area=nucleus_area+tmp_area;                           
          if polygon_intersect.geom_type == 'MultiPolygon':                                 
            for p in polygon_intersect:
              polygon_intersect_points =list(zip(*p.exterior.coords.xy));                                   
              has_value,one_polygon_mask=getMatrixValue(polygon_intersect_points,patch_min_x_pixel,patch_min_y_pixel);
              if(has_value):
                initial_grid = initial_grid | one_polygon_mask; 
                findPixelWithinPolygon=True;                                                                    
          elif polygon_intersect.geom_type == 'Polygon':               
            polygon_intersect_points =list(zip(*polygon_intersect.exterior.coords.xy));                                   
            has_value,one_polygon_mask=getMatrixValue(polygon_intersect_points,patch_min_x_pixel,patch_min_y_pixel);
            if(has_value):
              initial_grid = initial_grid | one_polygon_mask;  
              findPixelWithinPolygon=True;               
          else:               
            print "patch indexes %d Shape is not a polygon!!!" %tile_index;  
            print polygon_intersect.geom_type;
            #print polygon_intersect;
    
    if(special_case1=="both" and tumorFlag=="non_tumor"):        
      if(findPixelWithinPolygon):          
        mask = initial_grid.reshape(patch_size,patch_size);             
        for index1,row in enumerate(mask):
          for index2,pixel in enumerate(row):
            if (pixel):#this pixel is inside of segmented unclei polygon                     
              segment_img.append(grayscale_img_matrix[index1][index2]);
              segment_img_hematoxylin.append(Hematoxylin_img_matrix[index1][index2]);     
               
      percent_nuclear_material =float((nucleus_area/patch_polygon_area2)*100);  
             
      if (len(segment_img)>0):          
        segment_mean_grayscale_intensity= np.mean(segment_img);
        segment_std_grayscale_intensity= np.std(segment_img);         
        segment_mean_hematoxylin_intensity= np.mean(segment_img_hematoxylin);
        segment_std_hematoxylin_intensity= np.std(segment_img_hematoxylin);                            
      else:
        segment_mean_grayscale_intensity="n/a";
        segment_std_grayscale_intensity="n/a";
        segment_mean_hematoxylin_intensity="n/a";
        segment_std_hematoxylin_intensity="n/a";               
       
      if (len(Flatness_list)>0):
        Flatness_segment_mean= np.mean(Flatness_list);
        Flatness_segment_std= np.std(Flatness_list); 
      else:
        Flatness_segment_mean="n/a";
        Flatness_segment_std="n/a";
              
      if (len(Perimeter_list)>0):
        Perimeter_segment_mean= np.mean(Perimeter_list);
        Perimeter_segment_std= np.std(Perimeter_list);  
      else:
        Perimeter_segment_mean="n/a";
        Perimeter_segment_std="n/a";
            
      if (len(Circularity_list)>0):
        Circularity_segment_mean= np.mean(Circularity_list);
        Circularity_segment_std= np.std(Circularity_list);  
      else:
        Circularity_segment_mean="n/a";
        Circularity_segment_std="n/a";
              
      if (len(r_GradientMean_list)>0):
        r_GradientMean_segment_mean= np.mean(r_GradientMean_list);
        r_GradientMean_segment_std= np.std(r_GradientMean_list);
      else:
        r_GradientMean_segment_mean="n/a";  
        r_GradientMean_segment_std="n/a";
        
      if (len(b_GradientMean_list)>0):
        b_GradientMean_segment_mean= np.mean(b_GradientMean_list);
        b_GradientMean_segment_std= np.std(b_GradientMean_list);
      else:
        b_GradientMean_segment_mean="n/a";
        b_GradientMean_segment_std="n/a";
          
      if (len(r_cytoIntensityMean_list)>0):
        r_cytoIntensityMean_segment_mean= np.mean(r_cytoIntensityMean_list);
        r_cytoIntensityMean_segment_std= np.std(r_cytoIntensityMean_list);
      else:
        r_cytoIntensityMean_segment_mean="n/a";
        r_cytoIntensityMean_segment_std="n/a";
          
      if (len(b_cytoIntensityMean_list)>0):
        b_cytoIntensityMean_segment_mean= np.mean(b_cytoIntensityMean_list);
        b_cytoIntensityMean_segment_std= np.std(b_cytoIntensityMean_list);
      else:
        b_cytoIntensityMean_segment_mean="n/a";
        b_cytoIntensityMean_segment_std="n/a";  
        
      if (len(Elongation_list)>0):
        Elongation_segment_mean= np.mean(Elongation_list);
        Elongation_segment_std= np.std(Elongation_list);
      else:
        Elongation_segment_mean="n/a";
        Elongation_segment_std="n/a";             
      
      #convert area to physical area image_width,image_height,mpp-x,mpp-p      
      patch_polygon_area_new=patch_polygon_area2*factor;
      nucleus_area_new = nucleus_area*factor;
      patch_area_seleted_percentage=float((patch_polygon_area2/patch_polygon_area0)*100);
      
      print case_id,image_width,image_height,user,title_index,patch_min_x_pixel,patch_min_y_pixel,patch_size,patch_polygon_area_new,tumorFlag,nucleus_area_new,percent_nuclear_material,grayscale_patch_mean,grayscale_patch_std,Hematoxylin_patch_mean,Hematoxylin_patch_std,segment_mean_grayscale_intensity,segment_std_grayscale_intensity,segment_mean_hematoxylin_intensity,segment_std_hematoxylin_intensity,Flatness_segment_mean,Flatness_segment_std,Perimeter_segment_mean,Perimeter_segment_std,Circularity_segment_mean,Circularity_segment_std,r_GradientMean_segment_mean,r_GradientMean_segment_std,b_GradientMean_segment_mean,b_GradientMean_segment_std,r_cytoIntensityMean_segment_mean,r_cytoIntensityMean_segment_std,b_cytoIntensityMean_segment_mean,b_cytoIntensityMean_segment_std,Elongation_segment_mean,Elongation_segment_std; 
      print "\n"; 
      saveFeatures2MongoDB(case_id,image_width,image_height,mpp_x,mpp_y,user,title_index,patch_min_x_pixel,patch_min_y_pixel,patch_size,patch_polygon_area_new,patch_area_seleted_percentage,tumorFlag,nucleus_area_new,percent_nuclear_material,grayscale_patch_mean,grayscale_patch_std,Hematoxylin_patch_mean,Hematoxylin_patch_std,segment_mean_grayscale_intensity,segment_std_grayscale_intensity,segment_mean_hematoxylin_intensity,segment_std_hematoxylin_intensity,Flatness_segment_mean,Flatness_segment_std,Perimeter_segment_mean,Perimeter_segment_std,Circularity_segment_mean,Circularity_segment_std,r_GradientMean_segment_mean,r_GradientMean_segment_std,b_GradientMean_segment_mean,b_GradientMean_segment_std,r_cytoIntensityMean_segment_mean,r_cytoIntensityMean_segment_std,b_cytoIntensityMean_segment_mean,b_cytoIntensityMean_segment_std,Elongation_segment_mean,Elongation_segment_std);      
  #####################################################################
          
  print '--- process image_list  ---- ';   
  for item  in image_list:  
    case_id=item[0];
    user=item[1];  
     
    prefix_list=findPrefixList(case_id);
    if(len(prefix_list))<1:
      print "can NOT find prefix of this image!"
      exit();  
         
    comp_execution_id=getCompositeDatasetExecutionID(case_id);
    if(comp_execution_id==""):
      print "Composite dataset for this image is NOT available.";  
      continue;
    print "comp_execution_id is:" + str(comp_execution_id);
    
    humanMarkupList_tumor,humanMarkupList_non_tumor=findTumor_NonTumorRegions(case_id,user); 
    if(len(humanMarkupList_tumor) ==0 and humanMarkupList_non_tumor==0):
      print "No tumor or non tumor regions has been marked in this image by user %s." % user;
      continue; 
      
    #create local folder
    local_img_folder = os.path.join(local_dataset_folder, case_id);   
    if not os.path.exists(local_img_folder):
      print '%s folder do not exist, then create it.' % local_img_folder;
      os.makedirs(local_img_folder);  
       
    image_file_name=case_id+".svs";
    image_file = os.path.join(local_image_folder, image_file_name);         
    if not os.path.isfile(image_file):
      print "image svs file is not available, then download it to local folder.";
      img_path=findImagePath(case_id);
      full_image_file = os.path.join(remote_image_folder, img_path);      
      subprocess.call(['scp', full_image_file,local_image_folder]);   
       
    image_file = os.path.join(local_image_folder, image_file_name);
    print image_file;    
    try:
      img = openslide.OpenSlide(image_file);      
    except Exception as e: 
      print(e);
      continue; 
      
    image_width =img.dimensions[0];
    image_height =img.dimensions[1]; 
    #get image mpp-x and mpp-y
    for mpp_data in images.find({"case_id":case_id},{"mpp-x":1,"mpp-y":1,"_id":0}): 
      mpp_x=mpp_data["mpp-x"]; 
      mpp_y=mpp_data["mpp-y"];
      break;
    print " ==== image_width,image_height,mpp-x,mpp-p === ";
    print image_width,image_height,mpp_x,mpp_y
    
    #copy composite dataset to local folder  
    remote_img_folder = os.path.join(remote_dataset_folder, case_id);  
    for prefix in prefix_list:   
      detail_remote_folder = os.path.join(remote_img_folder, prefix); 
      detail_local_folder  = os.path.join(local_img_folder, prefix);    
      if not os.path.exists(detail_local_folder):
        print '%s folder do not exist, then create it.' % detail_local_folder;
        os.makedirs(detail_local_folder);        
      if os.path.isdir(detail_local_folder) and len(os.listdir(detail_local_folder)) > 0: 
        print " all csv and json files of this image have been copied from data node.";      
      else:
        subprocess.call(['scp', detail_remote_folder+'/*.json',detail_local_folder]);
        subprocess.call(['scp', detail_remote_folder+'/*features.csv',detail_local_folder]);
    
    #get image meta data
    #image_width,image_height = getImageMetaData(local_img_folder,prefix_list);
    unique_tile_min_point_list=findUniqueTileList(local_img_folder,prefix_list);
    
      
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor: 
      for index,tile_min_point in enumerate(unique_tile_min_point_list):  
        tile_width,tile_height = getTileMetaData(tile_min_point,local_img_folder,prefix_list);       
        tile_minx=tile_min_point[0];
        tile_miny=tile_min_point[1]; 
        x1t=float(tile_minx)/float(image_width);
        y1t=float(tile_miny)/float(image_height); 
        x2t=float(tile_minx+tile_width)/float(image_width);
        y2t=float(tile_miny+tile_height)/float(image_height);
        tile_polygon_0=[[x1t,y1t],[x2t,y1t],[x2t,y2t],[x1t,y2t],[x1t,y1t]];       
        x=tile_min_point[0];
        y=tile_min_point[1];
        tmp_string="_x"+str(x)+"_y" + str(y); 
        tile_item_array=[];
        for prefix in prefix_list:   
          detail_local_folder  = os.path.join(local_img_folder, prefix);
          for csv_json_file in os.listdir(detail_local_folder):   
            if csv_json_file.endswith("features.csv") and csv_json_file.find(tmp_string) <> -1:#find it! 
              tmp_obj_list=read_csv_data_file(detail_local_folder,csv_json_file);       
              tile_item_array.extend(tmp_obj_list);           
           
        i_range=tile_width/patch_size;
        j_range=tile_height/patch_size;                    
        for i in range(0,i_range):
          for j in range(0,j_range):
            x1=float(tile_minx+i*patch_size)/float(image_width);
            y1=float(tile_miny+j*patch_size)/float(image_height);
            x2=x1+float(patch_size)/float(image_width);
            y2=y1+float(patch_size)/float(image_height);            
            if x1>1.0:
              x1=1.0;
            if x1<0.0:
              x1=0.0; 
            if x2>1.0:
              x2=1.0;            
            if x2<0.0:
              x2=0.0;            
            if y1>1.0:
              y1=1.0;
            if y1<0.0:
              y1=0.0; 
            if y2>1.0:
              y2=1.0;
            if y2<0.0:
              y2=0.0;          
            patch_polygon_0=[[x1,y1],[x2,y1],[x2,y2],[x1,y2],[x1,y1]];            
            tmp_poly=[tuple(i1) for i1 in patch_polygon_0];
            tmp_polygon = Polygon(tmp_poly);
            patch_polygon = tmp_polygon.buffer(0); 
             
            patch_polygon_area0 =patch_polygon.area;          
            patch_polygon_area1=0.0;
            patch_polygon_area2=0.0;
            
            patchHumanMarkupRelation_tumor="disjoin";
            patchHumanMarkupRelation_nontumor="disjoin";  
            patch_humanmarkup_intersect_polygon_tumor = Polygon([(0, 0), (1, 1), (1, 0)]);
            patch_humanmarkup_intersect_polygon_nontumor = Polygon([(0, 0), (1, 1), (1, 0)]);
          
            for humanMarkup in humanMarkupList_tumor:                         
              if (patch_polygon.within(humanMarkup)):              
                patchHumanMarkupRelation_tumor="within";
                tumor_related_patch=True;
                patch_polygon_area1=patch_polygon.area;
                break;
              elif (patch_polygon.intersects(humanMarkup)):                
                patchHumanMarkupRelation_tumor="intersect";  
                patch_humanmarkup_intersect_polygon_tumor=humanMarkup;
                tumor_related_patch=True;
                polygon_intersect=patch_polygon.intersection(humanMarkup);
                patch_polygon_area1=polygon_intersect.area;
                break;
              else:               
                patchHumanMarkupRelation_tumor="disjoin";           
            
            for humanMarkup2 in humanMarkupList_non_tumor:                        
              if (patch_polygon.within(humanMarkup2)):              
                patchHumanMarkupRelation_nontumor="within";
                non_tumor_related_patch=True;
                patch_polygon_area2=patch_polygon.area;
                break;
              elif (patch_polygon.intersects(humanMarkup2)):                
                patchHumanMarkupRelation_nontumor="intersect";  
                patch_humanmarkup_intersect_polygon_nontumor=humanMarkup2;
                non_tumor_related_patch=True;
                polygon_intersect=patch_polygon.intersection(humanMarkup2);
                patch_polygon_area2=polygon_intersect.area;
                break;
              else:               
                patchHumanMarkupRelation_nontumor="disjoin";          
                      
            #only calculate features within/intersect tumor/non tumor region           
            if(patchHumanMarkupRelation_tumor=="disjoin" and patchHumanMarkupRelation_nontumor=="disjoin"):                     
              continue;  
          
            patch_min_x=int(x1*image_width);
            patch_min_y=int(y1*image_height); 
            patch_area1_seleted_percentage=float((patch_polygon_area1/patch_polygon_area0)*100); 
            patch_area2_seleted_percentage=float((patch_polygon_area2/patch_polygon_area0)*100);  
            #if selected patch area is too small, skip this patch
            if patch_area1_seleted_percentage<1.0 and patch_area2_seleted_percentage <1.0:
              continue  
                          
            #if patch_min_x<>13312 or patch_min_y<>70656:
            #  continue 
                                  
            nuclues_item_list=[];          
            for tile_item in tile_item_array:
              is_intersects=False;
              is_within=False;
              computer_polygon =tile_item[0]; 
              computer_polygon0 =tile_item[9];
              if (computer_polygon.within(patch_polygon)): 
                is_within=True;
              if (computer_polygon.intersects(patch_polygon)): 
                is_intersects=True;         
              if(is_within or is_intersects):
                #filter to eliminate invalid  nuclues_polygon  
                validity=explain_validity(computer_polygon0);            
                if (validity=="Valid Geometry"):                                                  
                  nuclues_item_list.append(tile_item);               
                else:
                  print "find invalid geometry!";  
                  print validity;
                  logging.debug('find invalid geometry.'); 
                  logging.debug(validity); 
                  
            nuclear_item_list=removeOverlapPolygon(nuclues_item_list)              
            executor.submit(process_one_patch,case_id,user,index,patch_polygon_area0,patch_polygon_area1,patch_polygon_area2,image_width,image_height,mpp_x,mpp_y,patch_polygon_0,patchHumanMarkupRelation_tumor,patchHumanMarkupRelation_nontumor,patch_humanmarkup_intersect_polygon_tumor,patch_humanmarkup_intersect_polygon_nontumor,nuclear_item_list);                                                                 
    img.close();  
  exit();  
 
