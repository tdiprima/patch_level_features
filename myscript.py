import os
import subprocess

case_id = 'PC_052_0_1'
username = ''
work_dir = "/data1/tdiprima/dataset"
csv_file_path = "nfs004:/data/shared/bwang/composite_dataset"


def assure_path_exists(path):
    m_dir = os.path.dirname(path)
    if not os.path.exists(m_dir):
        os.makedirs(m_dir)


def get_file_list(substr):
    """
    Find lines in file containing substring.
    Return list.
    :param substr:
    :return:
    """
    lines = []
    with open('config/csv_file_path.list') as f:
        for line in f:
            line = line.strip()
            if substr in line:
                lines.append(line)
    f.close()
    return lines


assure_path_exists(case_id)


# Get list of csv files containing features for this case_id
my_list = get_file_list(case_id)

for my_dir in my_list:
    print my_dir

# os.system has been deprecated in favor of subprocess
# subprocess.call(['scp', detail_remote_folder + '/*.json', detail_local_folder]);
# subprocess.call(['scp', detail_remote_folder + '/*features.csv', detail_local_folder]);
