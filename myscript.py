import os
import sys
import argparse
import subprocess
from pathlib import Path
from pymongo import MongoClient, errors


def assure_path_exists(path):
    m_dir = os.path.dirname(path)
    if not os.path.exists(m_dir):
        os.makedirs(m_dir)


def mongodb_connect(client_uri):
    try:
        return MongoClient(client_uri, serverSelectionTimeoutMS=1)
    except errors.ConnectionFailure:
        print("Failed to connect to server {}".format(client_uri))
        exit(1)


def get_file_list(substr, filepath):
    """
    Find lines in file containing substring.
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


def rsync_data_src():
    # Get list of csv files containing features for this case_id
    csv_paths = get_file_list(case_id, 'config/csv_file_path.list')

    for csv_dir1 in csv_paths:
        source_dir = os.path.join(csv_file_path, csv_dir1)
        # copy all *.json and *features.csv files
        m_args = list(["rsync", "-ar", "--include", "*features.csv", "--include", "*.json"])
        # m_args = list(["rsync", "-avz", "--include", "*features.csv", "--include", "*.json"])
        m_args.append(source_dir)
        m_args.append(work_dir)
        print("executing " + ' '.join(m_args))
        subprocess.call(m_args)

    my_file = Path(os.path.join(work_dir, (case_id + '.svs')))
    if not my_file.is_file():
        svs_list = get_file_list(case_id, 'config/image_path.list')
        svs_path = os.path.join(svs_image_path, svs_list[0])
        print("executing scp", svs_path, work_dir)
        subprocess.check_call(['scp', svs_path, work_dir])


def get_composite_exec_id():
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
        query = {"image.case_id": case_id,
                 "provenance.analysis_execution_id": {'$regex': 'composite_dataset', '$options': 'i'}}
        m_dict = coll.find_one(query)
        client.close()
    except errors.ServerSelectionTimeoutError as err:
        print(err)
        exit(1)
    return m_dict['provenance']['analysis_execution_id']


def get_tumor_markup():
    """
    Pretty self-explanatory
    :return:
    """
    execution_id = (user_name + "_Tumor_Region")
    try:
        client = mongodb_connect('mongodb://' + args["db_host"] + ':27017')
        client.server_info()  # force connection, trigger error to be caught
        db = client.quip
        coll = db.objects
        filter_q = {
                    'provenance.image.case_id': case_id,
                    'provenance.analysis.execution_id': execution_id
                }
        projection_q = {
                    'geometry': 1,
                    '_id': 0
                }
        m_dict = coll.find(filter_q, projection_q)
        for item in m_dict:
            print(item)
        client.close()
    except TypeError as err:
        print(err)
        exit(1)
    except errors.ServerSelectionTimeoutError as err:
        print(err)
        exit(1)


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
assure_path_exists(work_dir)
rsync_data_src()
composite_exec_id = get_composite_exec_id()
get_tumor_markup()
