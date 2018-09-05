import os
import json

path = '.'

files = os.listdir(path)
for name in files:
    print(name)

# Read JSON data into the datastore variable
# if filename:
#     with open(filename, 'r') as f:
#         datastore = json.load(f)

