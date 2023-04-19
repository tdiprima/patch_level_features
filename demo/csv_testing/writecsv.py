import json
import csv


# f = open('data.json')
# data = json.load(f)
# f.close()

# Create new file
# open('data.csv', 'a').close()

# f = csv.writer(open("test.csv", "wb+"))
# f.close()

# f = open('data.csv')
# csv_file = csv.writer(f)
# for item in data:
#     f.writerow(item)
#
# f.close()

# https://docs.python.org/3.3/tutorial/datastructures.html
# list(tel.keys())

# https://stackoverflow.com/questions/1871524/how-can-i-convert-json-to-csv

def flattenjson(b, delim):
    val = {}
    for i in b.keys():
        if isinstance(b[i], dict):
            get = flattenjson(b[i], delim)
            # for key, val in get.items():
            for j in get.keys():
                val[i + delim + j] = get[j]
        else:
            val[i] = b[i]

    return val
