# This script is designed to traverse a directory and its subdirectories, listing and sorting files with
# .json and .csv extensions.
import os


def get_data_files():
    filenames = os.listdir(SLIDE_DIR)  # get all files' and folders' names in directory

    folders = []
    for filename in filenames:  # loop through all the files and folders
        ppath = os.path.join(os.path.abspath(SLIDE_DIR), filename)
        if os.path.isdir(ppath):  # check whether the current object is a folder or not
            folders.append(ppath)

    folders.sort()
    print('subfolders: ', len(folders))

    json_files = []
    csv_files = []
    for index, filename in enumerate(folders):
        # print(index, filename)
        files = os.listdir(filename)
        for name in files:
            ppath = os.path.join(os.path.abspath(filename), name)
            if name.endswith('json'):
                json_files.append(ppath)
            elif name.endswith('csv'):
                csv_files.append(ppath)

    print('json_files: ', len(json_files))
    print('csv_files: ', len(csv_files))

    json_files.sort()
    csv_files.sort()
    return json_files, csv_files


SLIDE_DIR = ''
# Fetch list of data files
JSON_FILES, CSV_FILES = get_data_files()
