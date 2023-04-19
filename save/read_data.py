# Reads CSV files from directories, skips empty files, and returns list of dataframes.
# Then filters dataframes with polygons within or intersecting with specified tumor polygons.
import os
import time

import pandas
from shapely.geometry import Polygon, Point, MultiPoint


def read_data():
    """
    Get all the things.
    :return:
    """
    ret_list = []
    start_time = time.time()

    try:
        for csv_dir1 in CSV_REL_PATHS:
            local = os.path.join(WORK_DIR, csv_dir1)
            if os.path.isdir(local) and len(os.listdir(local)) > 0:
                feature_filename_list = [f for f in os.listdir(local) if f.endswith('features.csv')]
                for ff in feature_filename_list:
                    # Read each file
                    data_frame = pandas.read_csv(os.path.join(local, ff))
                    # Skip if file is empty
                    if data_frame.empty:
                        continue
                    # Return list of data frames
                    ret_list.append(
                        data_frame)  # Return list of polygons  # val = data_frame['Polygon'].values[0]  # ply = string_to_polygon(val)  # ret_list.append(ply)

    except Exception as ex:
        print('Error in read_data: ', ex)
        exit(1)

    elapsed_time = time.time() - start_time
    print('Runtime read_data: ')
    print(time.strftime("%H:%M:%S", time.gmtime(elapsed_time)))

    return ret_list


def get_polygons_within_tumors(data_frames, tumor_poly_list):
    """

    :param data_frames:
    :param tumor_poly_list:
    :return:
    """
    start_time = time.time()
    rtn_list = []

    within = 0
    intersects = 0
    disjoin = 0
    for tumor_roi in tumor_poly_list:
        for df in data_frames:
            val = df['Polygon'].values[0]
            poly = string_to_polygon(val)
            if poly.within(tumor_roi):
                rtn_list.append(df)
                within += 1
            elif poly.intersects(tumor_roi):
                rtn_list.append(df)
                intersects += 1
            elif poly.disjoint(tumor_roi):
                disjoin += 1

    print('within', within)
    print('intersects', intersects)
    print('disjoin', disjoin)

    elapsed_time = time.time() - start_time
    print('Runtime get_polygons_within_tumors: ')
    print(time.strftime("%H:%M:%S", time.gmtime(elapsed_time)))

    return rtn_list


def string_to_polygon(poly_data):
    """
    Convert Polygon string to polygon
    :param poly_data:
    :return:
    """
    points_list = []

    tmp_str = str(poly_data)
    tmp_str = tmp_str.replace('[', '')
    tmp_str = tmp_str.replace(']', '')
    split_str = tmp_str.split(':')
    a = 0.0
    b = 0.0

    try:
        for i in range(0, len(split_str) - 1, 2):
            a = float(split_str[i])
            b = float(split_str[i + 1])
            # Normalize points
            point = [a / float(IMAGE_WIDTH), b / float(IMAGE_HEIGHT)]
            m_point = Point(point)
            points_list.append(m_point)
        # Create a Polygon
        m = MultiPoint(points_list)
        m_polygon = Polygon(m)
    except Exception as ex:
        m_polygon = None
        print(a, b)
        print("strlen: ", len(split_str))
        print('Error in string_to_polygon', ex)
        exit(1)

    return m_polygon


CSV_REL_PATHS = []
WORK_DIR = ''
IMAGE_WIDTH = 1
IMAGE_HEIGHT = 1

# huge_list = read_data()
# print('len huge_list: ', len(huge_list))
# smaller_list = get_polygons_within_tumors(huge_list, tumor_poly_list)
# print('len smaller_list: ', len(smaller_list))
# del huge_list
# gc.collect()
