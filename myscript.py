import sys
import pandas
import numpy as np

# This program will take arguments:
# slide_name
# user_name
# tile_size
# db_host

program_name = sys.argv[0]
arguments = sys.argv[1:]
count = len(arguments)

# check command-line arguments
if count != 5:
    print 'Usage: python ' + program_name + ' slide_name user_name tile_size db_host'
    # sys.exit(1)


def readfile_demo(filename):
    # temporarily using 1 input file
    df = pandas.read_csv(filename)

    for name, values in df.iteritems():
        print '{name}: {type}'.format(name=name, type=type(values[0]))
        # print '{name}: {value}'.format(name=name, value=values[0])

    # Convert Polygon string to array of float values
    str1 = df['Polygon'][0]

    if str1.startswith('[') and str1.endswith(']'):
        # slice first and last
        str2 = str1[1:-1]

    print str2

    arr = np.fromstring(str2, dtype=float, sep=':')
    print arr


filename = 'input_demo.csv'
readfile_demo(filename)
