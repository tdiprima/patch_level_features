# Compare patch by patch, the patch level features from Bridge's implementation
# with those from Tammy's implementation [get the difference]
import csv

import numpy as np
from pymongo import MongoClient

# RUN PGM FOR ONE CASE_ID
# TODO: Enter case_id and db_host!
case_id = ''
patch_size = '512'
db_host = ''
# input_collection = 'test_features_td'
input_collection = 'test1_features_td'
# output_file = 'output.csv'
output_file = 'output1.csv'


def is_number(s):
    try:
        float(s)  # for int, long and float
    except ValueError:
        try:
            complex(s)  # for complex
        except ValueError:
            return False

    return True


def get_data():
    client = MongoClient(db_host)
    db = client.quip_comp
    bridge = db.patch_level_features
    me = db[input_collection]

    my_data = []
    fields = ['case_id', 'patch_size', 'patch_min_x_pixel', 'patch_min_y_pixel', 'nucleus_area',
              'percent_nuclear_material', 'grayscale_patch_mean', 'grayscale_patch_std',
              'hematoxylin_patch_mean', 'hematoxylin_patch_std', 'flatness_segment_mean', 'flatness_segment_std',
              'perimeter_segment_mean', 'perimeter_segment_std', 'circularity_segment_mean', 'circularity_segment_std',
              'elongation_segment_mean', 'elongation_segment_std', 'r_GradientMean_segment_mean',
              'r_GradientMean_segment_std', 'b_GradientMean_segment_mean', 'b_GradientMean_segment_std',
              'r_cytoIntensityMean_segment_mean', 'r_cytoIntensityMean_segment_std',
              'b_cytoIntensityMean_segment_mean', 'b_cytoIntensityMean_segment_std']
    my_data.append(fields)

    for doc in bridge.find({'case_id': case_id}):
        x = doc['patch_min_x_pixel']
        y = doc['patch_min_y_pixel']
        items = me.find_one({'patch_min_x_pixel': x, 'patch_min_y_pixel': y})
        if items is not None:
            row_vals = [case_id, patch_size, x, y]
            start = len(row_vals)
            stop = len(fields)
            for x in range(start, stop):
                name = fields[x]
                try:
                    val1 = doc[name]
                except KeyError:
                    # Capitalize field name
                    val1 = doc[name.capitalize()]
                val2 = items[name]
                # Compare numbers
                if not is_number(val1) or not is_number(val2):
                    print('is_number()', val1, val2)
                    # print("Is NaN : ", np.isnan(val1))
                    # print("Is NaN : ", np.isnan(val2), "\n")
                else:
                    my_float = abs(val1 - val2)
                    # my_float = round(float(my_float), 7)

                    if np.isnan(my_float) or not is_number(my_float):
                        print('Result is not number', my_float)
                    else:
                        row_vals.append(my_float)

            my_data.append(row_vals)

    client.close()

    my_file = open(output_file, 'w')
    with my_file:
        writer = csv.writer(my_file)
        writer.writerows(my_data)

    print("Writing complete")


get_data()

exit(0)

