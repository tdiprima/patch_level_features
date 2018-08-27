import os
import subprocess

case_id = 'PC_052_0_1'
username = ''
work_dir = "/data1/tdiprima/dataset"
work_dir = os.path.join(work_dir, case_id)
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


def rsync_data_src():
    # Get list of csv files containing features for this case_id
    csv_paths = get_file_list(case_id)

    for csv_dir1 in csv_paths:
        source_dir = os.path.join(csv_file_path, csv_dir1)

        # copy all *.json files
        # args = ["rsync", "-avz", "--include", "*features.csv", "--include", "*.json"]
        args = ["rsync", "-ar", "--include", "*features.csv", "--include", "*.json"]
        args.append(source_dir)
        args.append(work_dir + os.sep)
        print "executing " + ' '.join(args)
        # subprocess.call(args)


assure_path_exists(work_dir)
rsync_data_src()
