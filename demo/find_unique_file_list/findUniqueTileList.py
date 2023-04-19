"""
This script identifies unique tile coordinates by parsing JSON metadata files in a hierarchical folder
structure, based on a specified case ID and prefixes, and prints the unique tile coordinate list.
"""
import csv
import json
import os


def find_unique_tile_list(local_img_folder, prefix_list):
    """
    The sets module is used here for removing duplicates from a sequence.
    :param local_img_folder:
    :param prefix_list:
    :return:
    """
    tile_min_point_list = []
    for prefix in prefix_list:
        detail_local_folder = os.path.join(local_img_folder, prefix)
        if os.path.isdir(detail_local_folder) and len(os.listdir(detail_local_folder)) > 0:
            json_filename_list = [f for f in os.listdir(detail_local_folder) if f.endswith('.json')]
            for json_filename in json_filename_list:
                with open(os.path.join(detail_local_folder, json_filename)) as f:
                    data = json.load(f)
                    tile_minx = data["tile_minx"]
                    tile_miny = data["tile_miny"]
                    point = [tile_minx, tile_miny]
                    tile_min_point_list.append(point)
    tmp_set = set(map(tuple, tile_min_point_list))
    # print('tmp_set', tmp_set)  # tuples all over the place
    map_output = map(list, tmp_set)  # nice, neat set of stuff

    # list_map_output = list(map_output)
    # print(len(list_map_output))

    return map_output


def find_prefix_list(work_dir, case_id):
    """
    Searches for and extracts a list of prefixes associated with a given case_id from a file named
    case_id_prefix.txt located in the specified work_dir directory.
    :param work_dir:
    :param case_id:
    :return:
    """
    prefix_list = []
    input_file = "case_id_prefix.txt"
    prefix_file = os.path.join(work_dir, input_file)
    print('prefix_file', prefix_file)
    with open(prefix_file, 'r') as my_file:
        reader = csv.reader(my_file, delimiter=',')
        my_list = list(reader)
        for each_row in my_list:
            file_path = each_row[0]  # path
            if file_path.find(case_id) != -1:  # find it!
                prefix_path = each_row[0]
                position_1 = prefix_path.rfind('/') + 1
                position_2 = len(prefix_path)
                prefix = prefix_path[position_1:position_2]
                print('prefix', prefix)
                prefix_list.append(prefix)
    return prefix_list


case_id = 'PC_051_0_1'
work_dir = '/data1/tdiprima'

prefix_list = find_prefix_list(work_dir, case_id)
local_dataset_folder = os.path.join(work_dir, 'dataset')
local_img_folder = os.path.join(local_dataset_folder, case_id)

unique_tile_min_point_list = find_unique_tile_list(local_img_folder, prefix_list)

for index, tile_min_point in enumerate(unique_tile_min_point_list):
    print(index, tile_min_point)
