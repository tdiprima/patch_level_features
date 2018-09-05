import os
import json
import pandas

path = '/data1/tdiprima/dataset/PC_051_0_1'
filenames = os.listdir(path)  # get all files' and folders' names in directory

folders = []
for filename in filenames:  # loop through all the files and folders
    ppath = os.path.join(os.path.abspath(path), filename)
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

for n, jfile in enumerate(json_files):
    with open(jfile, 'r') as f:
        print(n)
        # Read JSON data into the dict1 variable
        dict1 = json.load(f)
        str = dict1['out_file_prefix']
        print(str)
        cfile = csv_files[n]
        print(cfile)

        if str not in cfile:
            print('There should be 1 json file for 1 csv file.')
            exit(1)
        else:
            print('All good.')

        # Read CSV data into the dataframe variable
        df = pandas.read_csv(cfile)
        print('Perimeter', df['Perimeter'])
    f.close()

