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
import matplotlib.pyplot as plt
import datetime    
    
if __name__ == '__main__':
  if len(sys.argv)<2:
    print "usage:python generate_object_level_histogram.py case_id user";
    exit(); 
    
  '''
  object area //Should be physical size. Use the mpp values of images.
  object elongation
  object circularity 
  object grayscale intensity
  '''
      
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
  
  #my_home="/data1/bwang"  
  my_home="/home/bwang/patch_level"
  picture_folder = os.path.join(my_home, 'picture');
  
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
    
  collection_saved= db2.patch_level_features_run2;
  object_level_histogram = db2.object_level_histogram; 
  
  image_width=0;
  image_height=0; 
  mpp_x=0.0;
  mpp_y=0.0;   
  tolerance=1.0;   
  
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
  def getMatrixValue(poly_in,patch_min_x_pixel,patch_min_y_pixel,points):          
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
  
  #########################################
  def saveHistogram(case_id,feature,data_range,hist_count_array,bin_edges_array):
    dict_patch = collections.OrderedDict();
    dict_patch['case_id'] = case_id
    dict_patch['feature'] = feature
    dict_patch['data_range'] = data_range    
    dict_patch['hist_count_array'] = hist_count_array
    dict_patch['bin_edges_array'] = bin_edges_array    
    dict_patch['date'] = datetime.datetime.now();    
    object_level_histogram.insert_one(dict_patch);   
  #########################################
  
  #########################################
  def getGrayscale(computer_polygon):
    computer_polygon_bound=computer_polygon.bounds;
    #print computer_polygon_bound;
    #print image_width,image_height;
    computer_polygon_min_x_pixel =int(computer_polygon_bound[0]*image_width);
    computer_polygon_min_y_pixel =int(computer_polygon_bound[1]*image_height);    
    x1=int(computer_polygon_bound[0]*image_width);
    y1=int(computer_polygon_bound[1]*image_height);
    x2=int(computer_polygon_bound[2]*image_width);
    y2=int(computer_polygon_bound[3]*image_height); 
    computer_polygon_width=x2-x1 ;
    computer_polygon_height=y2-y1;
    #print computer_polygon_width,computer_polygon_height;
    
    x, y = np.meshgrid(np.arange(computer_polygon_width), np.arange(computer_polygon_height));
    x, y = x.flatten(), y.flatten();
    points = np.vstack((x,y)).T ;
       
    try:
      computer_polygon_img= img.read_region((computer_polygon_min_x_pixel, computer_polygon_min_y_pixel), 0, (computer_polygon_width, computer_polygon_height));
    except openslide.OpenSlideError as detail:
      print 'Handling run-time error:', detail  
      exit();
    except Exception as e: 
      print(e);
      exit();        
          
    grayscale_img = computer_polygon_img.convert('L');            
    grayscale_img_matrix=np.array(grayscale_img);  
    #print  "grayscale_img_matrix";
    #print  grayscale_img_matrix;  
    initial_grid=np.full((computer_polygon_width*computer_polygon_height), False); 
    #print "initial_grid";
    #print initial_grid       
    findPixelWithinPolygon=False;
    computer_polygon_points =list(zip(*computer_polygon.exterior.coords.xy));    
    has_value,one_polygon_mask=getMatrixValue(computer_polygon_points,computer_polygon_min_x_pixel,computer_polygon_min_y_pixel,points); 
    if(has_value):
      initial_grid = initial_grid | one_polygon_mask; 
      findPixelWithinPolygon=True; 
      #print "initial_grid";
      #print initial_grid;
      
    segment_img=[];      
    if(findPixelWithinPolygon):          
      mask = initial_grid.reshape(computer_polygon_height,computer_polygon_width); 
      #print "mask"; 
      #print mask;           
      for index1,row in enumerate(mask):
        for index2,pixel in enumerate(row):
          if (pixel):#this pixel is inside of segmented unclei polygon                     
            segment_img.append(grayscale_img_matrix[index1][index2]); 
    
    #print "segment_img"; 
    #print segment_img;            
    if (len(segment_img)>0):          
      segment_mean_grayscale_intensity= np.mean(segment_img);                                 
    else:
      segment_mean_grayscale_intensity="n/a";
      
    return segment_mean_grayscale_intensity;      
  #########################################
  
          
  print '--- process image_list  ---- ';   
  for item  in image_list:  
    case_id=item[0];
    user=item[1];  
     
    prefix_list=findPrefixList(case_id);
    if(len(prefix_list))<1:
      print "can NOT find prefix of this image!"
      exit();     
    
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
    
    factor=float(image_width)*float(image_height)*mpp_x*mpp_y;
    
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
    
    unique_tile_min_point_list=findUniqueTileList(local_img_folder,prefix_list);    
    
    total_record_count=0;
    total_invalid_record_count=0;  
    nuclear_object_area_list=[];
    nuclear_object_circularity_list=[];
    nuclear_object_elongation_list=[];
    nuclear_object_grayscale_list=[];
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
        tmp_poly=[tuple(i1) for i1 in tile_polygon_0];
        tmp_polygon = Polygon(tmp_poly);
        tile_polygon = tmp_polygon.buffer(0);
        tileHumanMarkupRelation_tumor="disjoin";        
        
        for humanMarkup in humanMarkupList_tumor:                         
          if (tile_polygon.within(humanMarkup)):              
            tileHumanMarkupRelation_tumor="within";
            tumor_related_tile=True;            
            break;
          elif (tile_polygon.intersects(humanMarkup)):                
            tileHumanMarkupRelation_tumor="intersect";  
            tile_humanmarkup_intersect_polygon_tumor=humanMarkup;
            tumor_related_tile=True;
            tile_polygon=tile_polygon.intersection(humanMarkup);            
            break;
          else:               
            tileHumanMarkupRelation_tumor="disjoin";                
                      
        #only calculate features within/intersect tumor region           
        if(tileHumanMarkupRelation_tumor=="disjoin"):                     
          continue; 
             
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
                                  
        nuclues_item_list=[]; 
        invalid_polygon_count=0;         
        for tile_item in tile_item_array:
          is_intersects=False;
          is_within=False;
          computer_polygon =tile_item[0]; 
          computer_polygon0 =tile_item[9];
          if (computer_polygon.within(tile_polygon)): 
            is_within=True;
          if (computer_polygon.intersects(tile_polygon)): 
            is_intersects=True;         
          if(is_within or is_intersects):
            total_record_count+=1;
            #filter to eliminate invalid  nuclues_polygon  
            validity=explain_validity(computer_polygon0);            
            if (validity=="Valid Geometry"):                                                  
              nuclues_item_list.append(tile_item);               
            else:
              invalid_polygon_count+=1;
              total_invalid_record_count+=1;

        record_count =len(nuclues_item_list);  
        print "-------------------------------------------------------------------------------------";      
        print index,tile_minx,tile_miny,tile_width,tile_height,record_count,invalid_polygon_count;        
        if (record_count>0):                                                                         
          for item in nuclues_item_list: 
            computer_polygon=item[0];            
            Circularity_value=float(item[3]); 
            nuclear_object_circularity_list.append(Circularity_value);           
            Elongation_value=float(item[8]); 
            nuclear_object_elongation_list.append(Elongation_value);
            grayscale_mean=getGrayscale(computer_polygon); 
            if(grayscale_mean<>"n/a"):             
              nuclear_object_grayscale_list.append(grayscale_mean);  
            polygon_area= computer_polygon.area;
            nuclear_polygon_area=polygon_area*factor; 
            nuclear_object_area_list.append(nuclear_polygon_area);                         
            #print nuclear_polygon_area,Circularity_value,Elongation_value,grayscale_mean;
      '''
      bin_num=100;
      data_range="object level";
      hist_count_array=[];
      bin_edges_array=[];      
      feature='nucleus_area';
      n, bins, patches = plt.hist(nuclear_object_area_list,  bins=bin_num,facecolor='#0504aa',alpha=0.5)      
      plt.xlabel(feature +' micron square')
      plt.ylabel('Nucleus Object Count')
      plt.title("object level "+ feature+ ' Histogram of image '+ str(case_id))
      #Tweak spacing to prevent clipping of ylabel
      plt.subplots_adjust(left=0.15)
      plt.grid(True);
      plt.show();
      file_name="object_level_histogram_"+case_id+"_"+feature+".png";  
      graphic_file_path = os.path.join(picture_folder, file_name);
      plt.savefig(graphic_file_path); 
      for count in n:        
        hist_count_array.append(int(count));
      for bin_edge in bins:        
        bin_edges_array.append(float(bin_edge));     
      saveHistogram(case_id,feature,data_range,hist_count_array,bin_edges_array); 
      
      
      hist_count_array=[];
      bin_edges_array=[];
      feature='circularity';
      n, bins, patches = plt.hist(nuclear_object_circularity_list,  bins=bin_num ,facecolor='#0504aa',alpha=0.5)      
      plt.xlabel(feature)
      plt.ylabel('Nucleus Object Count')
      plt.title("object level "+ feature+ ' Histogram of image '+ str(case_id))
      #Tweak spacing to prevent clipping of ylabel
      plt.subplots_adjust(left=0.15)
      plt.grid(True);
      plt.show();
      file_name="object_level_histogram_"+case_id+"_"+feature+".png";  
      graphic_file_path = os.path.join(picture_folder, file_name);
      plt.savefig(graphic_file_path);
      for count in n:        
        hist_count_array.append(int(count));
      for bin_edge in bins:        
        bin_edges_array.append(float(bin_edge));     
      saveHistogram(case_id,feature,data_range,hist_count_array,bin_edges_array);
      
      hist_count_array=[];
      bin_edges_array=[];
      feature='elongation';
      n, bins, patches = plt.hist(nuclear_object_elongation_list,  bins=bin_num,facecolor='#0504aa',alpha=0.5)      
      plt.xlabel(feature)
      plt.ylabel('Nucleus Object Count')
      plt.title("object level "+ feature+ ' Histogram of image '+ str(case_id))
      #Tweak spacing to prevent clipping of ylabel
      plt.subplots_adjust(left=0.15)
      plt.grid(True);
      plt.show();
      file_name="object_level_histogram_"+case_id+"_"+feature+".png";  
      graphic_file_path = os.path.join(picture_folder, file_name);
      plt.savefig(graphic_file_path);
      for count in n:        
        hist_count_array.append(int(count));
      for bin_edge in bins:        
        bin_edges_array.append(float(bin_edge));     
      saveHistogram(case_id,feature,data_range,hist_count_array,bin_edges_array); 
      '''
      
      bin_num=100;
      data_range="object level";
      hist_count_array=[];
      bin_edges_array=[];      
      feature='grayscale_intensity';
      n, bins, patches = plt.hist(nuclear_object_grayscale_list,  bins=bin_num,facecolor='#0504aa',alpha=0.5)      
      plt.xlabel(feature)
      plt.ylabel('Nucleus Object Count')
      plt.title("object level "+ feature+ ' Histogram of image '+ str(case_id))
      #Tweak spacing to prevent clipping of ylabel
      plt.subplots_adjust(left=0.15)
      plt.grid(True);
      plt.show();
      file_name="object_level_histogram_"+case_id+"_"+feature+".png";  
      graphic_file_path = os.path.join(picture_folder, file_name);
      plt.savefig(graphic_file_path); 
      for count in n:        
        hist_count_array.append(int(count));
      for bin_edge in bins:        
        bin_edges_array.append(float(bin_edge));     
      saveHistogram(case_id,feature,data_range,hist_count_array,bin_edges_array);     
              
    img.close();  
  exit();  
 
