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


def str_to_arr(dataframe, elem_name, idx):
    """
    Convert Polygon string to array of float values
    :param dataframe:
    :param elem_name:
    :param idx:
    :return:
    """
    str1 = dataframe[elem_name][idx]
    str2 = ''

    if str1.startswith('[') and str1.endswith(']'):
        str2 = str1[1:-1]  # slice first and last

    if str2 != '':
        return np.fromstring(str2, dtype=float, sep=':')
    else:
        return None


def readfile_demo(filename):
    """
    Things we can do with this file
    :param filename:
    :return:
    """
    df = pandas.read_csv(filename)

    for name, values in df.iteritems():
        print '{name}: {type}'.format(name=name, type=type(values[0]))
        # print '{name}: {value}'.format(name=name, value=values[0])

        arr = str_to_arr(df, 'Polygon', 0)
        print arr


def readfile(filename):
    """
    Using 1 input file
    :param filename:
    :return:
    """
    df = pandas.read_csv(filename)


csv_file = 'input_demo.csv'
# readfile_demo(csv_file)
readfile(csv_file)
