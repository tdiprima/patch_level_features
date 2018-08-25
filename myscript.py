# Image and patient level features, within tumor regions

from __future__ import division
import sys
import pandas
import numpy as np
import statistics
import matplotlib.pyplot as plt

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
    tile_size = 512
    # sys.exit(1)


def str_to_arr(data_frame, elem_name, idx):
    """
    Convert Polygon string to array of float values
    :param data_frame:
    :param elem_name:
    :param idx:
    :return:
    """
    str1 = data_frame[elem_name][idx]
    str2 = ''

    if str1.startswith('[') and str1.endswith(']'):
        str2 = str1[1:-1]  # slice first and last

    if str2 != '':
        return np.fromstring(str2, dtype=float, sep=':')
    else:
        return None


def readfile_demo(filename):
    """
    Demonstrate ways in which to analyze the CSV file
    :param filename:
    :return:
    """
    df = pandas.read_csv(filename)

    print("*** COLUMN TYPES ***")
    for name, values in df.iteritems():
        print '{name}: {type}'.format(name=name, type=type(values[0]))
        # print '{name}: {value}'.format(name=name, value=values[0])

    print("*** POLYGON ***")
    arr = str_to_arr(df, 'Polygon', 0)
    print arr

    print("*** DESCRIBE ***")
    print(df.describe())

    # Look at the first 3 rows
    # small_df = df[:3]
    # small_df['AreaInPixels'].plot()

    # PLOT!
    ax = df['AreaInPixels'].plot()
    ax.set_xlabel("Num of Objects")
    ax.set_ylabel("AreaInPixels")


def something():
    """
    get markups (region segmentations) and do intersection
    :return:
    """
    print "hello"


def compute_rnm(data_frame):
    """
    ratio of nuclear material
    :param data_frame:
    :return:
    """
    # side_length = tile_size  # global
    # TODO: temporary, we're pretending patch is tile
    side_length = 2000  # either 2 or 4
    area_square = side_length * side_length
    # print "area_square: ", area_square
    total_polygon_area = data_frame['AreaInPixels'].sum()
    # print "total_polygon_area: ", total_polygon_area
    rnm = float(total_polygon_area / area_square)
    # print "ratio of nuclear material: ", rnm
    return rnm


def process_file(filename):
    """
    Process 1 input file
    :param filename:
    :return:
    """
    df = pandas.read_csv(filename)
    compute_rnm(df)


csv_file = 'input_demo.csv'
# readfile_demo(csv_file)
process_file(csv_file)
