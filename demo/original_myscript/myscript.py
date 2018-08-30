# Image and patient level features, within tumor regions

from __future__ import division
from __future__ import print_function
from shapely.geometry import Point
from shapely.geometry import Polygon
from shapely.geometry import box
import sys
import cv2
import numpy as np
import pandas
import matplotlib.pyplot as plt
plt.switch_backend('agg')

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
    print('Usage: python ' + program_name + ' slide_name user_name tile_size db_host')
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


def get_iterator(dict1):
    """
    Because dict.iterkeys(), dict.iteritems() and dict.itervalues()
    methods are not available in py3.
    :param dict1:
    :return:
    """
    try:
        # Python 2
        iter_obj = dict1.iteritems()
    except AttributeError:
        # Python 3
        iter_obj = iter(dict1.items())

    return iter_obj


def show_column_types(data_frame):
    """
    :param data_frame:
    :return:
    """
    iter_obj = get_iterator(data_frame)
    for name, values in iter_obj:
        print('{name}: {type}'.format(name=name, type=type(values[0])))
        # print '{name}: {value}'.format(name=name, value=values[0])


def readfile_demo(filename):
    """
    Demonstrate ways in which to analyze the CSV file
    :param filename:
    :return:
    """
    print("readfile_demo")
    data_frame = pandas.read_csv(filename)

    print("*** COLUMN TYPES ***")
    show_column_types(data_frame)

    print("*** POLYGON ***")
    arr = str_to_arr(data_frame, 'Polygon', 0)
    print(arr)

    print("*** DESCRIBE ***")
    print(data_frame.describe())

    # Look at the first 3 rows
    # small_df = df[:3]
    # small_df['AreaInPixels'].plot()

    # PLOT!
    ax = data_frame['AreaInPixels'].plot()
    ax.set_xlabel("Num of Objects")
    ax.set_ylabel("AreaInPixels")
    plt.show()


def compute_intersection():
    """
    get markup (region segmentation) and do intersection
    :return:
    """
    print("compute_intersection")


def compute_intersection_demo():
    """
    calculating area of polygon inside region
    :return:
    """
    print("compute_intersection_demo")
    # http://toblerity.org/shapely/manual.html
    a = Point(1, 1).buffer(1.5)
    b = Point(2, 1).buffer(1.5)
    c = a.intersection(b)
    print("intersect area (circles): ", c.area)

    # http://toblerity.org/shapely/manual.html#polygons
    a = Polygon([(0, 0), (1, 1), (1, 0)])
    b = Polygon([(0.5, 0.5), (1.5, 1.5), (1.5, 0.5)])
    c = a.intersection(b)
    print("intersect area (polygons): ", c.area)
    # poly = Polygon(list(zip(X[0], Y[0])))

    # a = box(0, 0, 3, 3)  # patch
    b = Polygon([(0, 0), (0, 2), (2, 2), (2, 0)])  # roi
    c = Polygon([(0.5, 0.5), (1.0, 1.0), (1.5, 0.5), (1.0, 0.0)])  # polygon
    d = c.intersection(b)
    print("poly area", c.area)
    print("intersect area (poly, roi): ", d.area)
    # WITHIN:
    # object's boundary and interior intersect only with the interior of the other
    # (not its boundary or exterior)
    print("poly within roi: ", c.within(b))
    # CROSSES:
    # interior of the object intersects the interior of the other but does not contain it...
    print("poly crosses roi: ", c.crosses(b))
    # DISJOINT: boundary and interior of the object do not intersect at all
    print("poly does not intersect roi: ", c.disjoint(b))


def is_within_roi():
    print("is_within_roi")
    b = box(0.0, 0.0, 1.0, 1.0)
    print(b)


def is_within_patch():
    print("is_within_patch")


def detect_bright_spots():
    """
    Detect bright spots (no staining) and ignore those areas in area computation
    :return:
    """
    # load the image, convert it to grayscale, and blur it
    print("detect_bright_spots")
    image = cv2.imread('img/detect_bright_spots.png')
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (11, 11), 0)
    # threshold the image to reveal light regions in the
    # blurred image
    # Pixel values p >= 200 are set to 255 (white)
    # Pixel values < 200 are set to 0 (black).
    thresh = cv2.threshold(blurred, 200, 255, cv2.THRESH_BINARY)[1]

    try:
        # show the output image
        cv2.imshow("Image", thresh)
        cv2.waitKey(0)
    except cv2.error as e:
        print("\nCan't display the image.\n", e)
        exit(1)


def compute_rnm(data_frame):
    """
    ratio of nuclear material
    :param data_frame:
    :return:
    """
    print("compute ratio of nuclear material")
    # side_length = tile_size  # global
    # TODO: temporary, we're pretending patch is tile
    side_length = 2048
    area_square = side_length * side_length
    # print "area_square: ", area_square
    total_polygon_area = data_frame['AreaInPixels'].sum()
    # print "total_polygon_area: ", total_polygon_area
    rnm = float(total_polygon_area / area_square)
    # print "ratio of nuclear material: ", rnm
    return rnm


csv_file = 'input_demo.csv'
readfile_demo(csv_file)

df = pandas.read_csv(csv_file)
compute_rnm(df)

compute_intersection_demo()

is_within_roi()

detect_bright_spots()
