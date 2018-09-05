import os
import json
import pandas

path = '.'
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
f1 = json_files[0]
f2 = csv_files[0]

# Read JSON data into the dict1 variable
print(f1)
if f1:
    with open(f1, 'r') as f:
        dict1 = json.load(f)
        print(dict1)
    f.close()

# Read CSV data into the dataframe variable
print(f2)
if f2:
    df = pandas.read_csv(f2)
    print(df)

