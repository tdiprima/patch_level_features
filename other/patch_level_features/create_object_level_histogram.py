import matplotlib.pyplot as plt
plt.switch_backend('agg')
import matplotlib.patches as patches
import matplotlib.path as path
import numpy as np
import collections
import sys
import os
import json 
import datetime
from pymongo import MongoClient


if __name__ == '__main__':
  if len(sys.argv)<0:
    print "usage:python create_object_level_histogram.py";
    exit();    
  
  #my_home="/data1/bwang"  
  my_home="/home/bwang/patch_level";
  
  picture_folder = os.path.join(my_home, 'object_level_plot'); 
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
  db2 = client[db_name2];    
  features_histogram = db2.features_histogram;  
    
  for record in features_histogram.find({'data_range':'object_level'},{"_id":0,"date":0,"data_range":0}):    
    case_id=record["case_id"]; 
    feature=record["feature"];
    if (feature=='nucleus_area'):
      feature_name="nucleus area (Micron square)"; 
    elif (feature=='elongation'):
      feature_name="elongation (Micron)"; 
    elif (feature=='circularity'):
      feature_name="circularity (Micron)";   
    else:  
      feature_name = feature;      
    n=record["hist_count_array"];
    bins=record["bin_edges_array"];
    print case_id,feature;       
    total_object_count=0;
    for count in n:
      total_object_count=total_object_count+ count;            
    fig, ax = plt.subplots()
    # get the corners of the rectangles for the histogram
    left = np.array(bins[:-1])
    right = np.array(bins[1:])
    bottom = np.zeros(len(left))
    top = bottom + n
    # we need a (numrects x numsides x 2) numpy array for the path helper
    # function to build a compound path
    XY = np.array([[left, left, right, right], [bottom, top, top, bottom]]).T
    # get the Path object
    barpath = path.Path.make_compound_path_from_polys(XY)
    # make a patch out of it
    patch = patches.PathPatch(barpath)
    ax.add_patch(patch)
    # update the view limits
    ax.set_xlim(left[0], right[-1])
    ax.set_ylim(bottom.min(), top.max())            
    plt.xlabel(feature_name)
    plt.ylabel('Object Count')
    plt.title("Object level "+ feature+ ' Histogram of image '+ str(case_id))
    #Tweak spacing to prevent clipping of ylabel
    plt.subplots_adjust(left=0.15)
    plt.grid(True);           
    # place a text box in upper left in axes coords
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    textstr="Total object count: " + str(total_object_count);
    ax.text(0.6, 0.95, textstr, transform=ax.transAxes, fontsize=10, verticalalignment='top', bbox=props);      
    #plt.show();       
    file_name="object_level_histogram_"+case_id+"_"+feature+".png";  
    graphic_file_path = os.path.join(picture_folder, file_name);
    plt.savefig(graphic_file_path); 
    plt.gcf().clear();      
  exit(); 
