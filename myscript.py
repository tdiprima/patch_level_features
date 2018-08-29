import os
import sys
import argparse
import subprocess
from shapely.geometry import Polygon, Point
from shapely.geometry import MultiPoint
from pathlib import Path
from pymongo import MongoClient, errors


def assure_path_exists(path):
    """
    If path exists, great.
    If not, then create it.
    :param path:
    :return:
    """
    m_dir = os.path.dirname(path)
    if not os.path.exists(m_dir):
        os.makedirs(m_dir)


def mongodb_connect(client_uri):
    """
    Connection routine
    :param client_uri:
    :return:
    """
    try:
        return MongoClient(client_uri, serverSelectionTimeoutMS=1)
    except errors.ConnectionFailure:
        print("Failed to connect to server {}".format(client_uri))
        exit(1)


def get_file_list(substr, filepath):
    """
    Find lines in data file containing substring.
    Return list.
    :param substr:
    :param filepath:
    :return:
    """
    lines = []
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if substr in line:
                lines.append(line)
    f.close()
    return lines


def copy_src_data(source_csv, source_svs, dest, m_caseid):
    """
    Copy data from nfs location to computation node.
    :param m_caseid:
    :param source_csv:
    :param source_svs:
    :param dest:
    :return:
    """
    # Get list of csv files containing features for this case_id
    csv_paths = get_file_list(m_caseid, 'config/csv_file_path.list')

    for csv_dir1 in csv_paths:
        source_dir = os.path.join(source_csv, csv_dir1)
        # copy all *.json and *features.csv files
        m_args = list(["rsync", "-ar", "--include", "*features.csv", "--include", "*.json"])
        # m_args = list(["rsync", "-avz", "--include", "*features.csv", "--include", "*.json"])
        m_args.append(source_dir)
        m_args.append(dest)
        print("executing " + ' '.join(m_args))
        subprocess.call(m_args)

    my_file = Path(os.path.join(dest, (m_caseid + '.svs')))
    if not my_file.is_file():
        svs_list = get_file_list(m_caseid, 'config/image_path.list')
        svs_path = os.path.join(source_svs, svs_list[0])
        print("executing scp", svs_path, dest)
        subprocess.check_call(['scp', svs_path, dest])


def get_composite_exec_id(m_caseid):
    """
    There is only one composite dataset (unique execution_id) in quip_comp
    database for each image.
    :return:
    """
    m_dict = {}
    try:
        client = mongodb_connect('mongodb://' + args["db_host"] + ':27017')
        client.server_info()  # force connection, trigger error to be caught
        db = client.quip_comp
        coll = db.metadata
        query = {"image.case_id": m_caseid,
                 "provenance.analysis_execution_id": {'$regex': 'composite_dataset', '$options': 'i'}}
        m_dict = coll.find_one(query)
        client.close()
    except errors.ServerSelectionTimeoutError as err:
        print(err)
        exit(1)
    return m_dict['provenance']['analysis_execution_id']


def get_tumor_markup(m_caseid):
    """
    Find what the pathologist circled as tumor.
    :return:
    """
    tumor_markup_list = []
    execution_id = (user_name + "_Tumor_Region")
    try:
        client = mongodb_connect('mongodb://' + args["db_host"] + ':27017')
        client.server_info()  # force connection, trigger error to be caught
        db = client.quip
        coll = db.objects
        filter_q = {
                    'provenance.image.case_id': m_caseid,
                    'provenance.analysis.execution_id': execution_id
                }
        projection_q = {
                    'geometry.coordinates': 1,
                    '_id': 0
                }
        print(filter_q, projection_q)
        cursor = coll.find(filter_q, projection_q)
        for item in cursor:
            # geometry.coordinates happens to be a list with one thing in it: a list! (of point coordinates).
            points = item["geometry"]["coordinates"][0]  # dictionary to list
            tumor_markup_list.append(points)
        client.close()
    except errors.ServerSelectionTimeoutError as err:
        print(err)
        exit(1)
    print("count: ", len(tumor_markup_list))
    return tumor_markup_list


def convert_to_polygons(markup_list):
    """
    Given a list of lists of point coordinates,
    convert the point coordinates to tuples
    and create a Polygon.
    Return list of polygons.
    :param markup_list:
    :return:
    """
    poly_list = []
    try:
        for coordinates in markup_list:
            points_list = []

            for point in coordinates:
                point = Point(point[0], point[1])
                points_list.append(point)
            m = MultiPoint(points_list)
            polygon = Polygon(m)
            poly_list.append(polygon)
    except Exception as ex:
        print(ex)
        exit(1)

    return poly_list


work_dir = "/data1/tdiprima/dataset"
csv_file_path = "nfs004:/data/shared/bwang/composite_dataset"
svs_image_path = "nfs001:/data/shared/tcga_analysis/seer_data/images"

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-s", "--slide_name", help="svs image name")
ap.add_argument("-u", "--user_name", help="user who identified tumor regions")
ap.add_argument("-b", "--db_host", help="database host")
ap.add_argument("-t", "--tile_size", type=int, help="tile size")
args = vars(ap.parse_args())
print(args)

if not len(sys.argv) > 1:
    program_name = sys.argv[0]
    lst = ['python', program_name, '-h']
    subprocess.call(lst)  # Show help
    exit(1)

case_id = args["slide_name"]
user_name = args["user_name"]
work_dir = os.path.join(work_dir, case_id) + os.sep

# Fetch data
# assure_path_exists(work_dir)
# copy_src_data(csv_file_path, svs_image_path, work_dir, case_id)

# Find what the pathologist circled as tumor
tumor_mark = get_tumor_markup(case_id)
tumor_mark = convert_to_polygons(tumor_mark)

# Get exec_id for polygons
# composite_exec_id = get_composite_exec_id()
