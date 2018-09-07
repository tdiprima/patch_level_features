# TOOK TOO LONG TO RUN. LIKE 1 HOUR.
# THAT'S WHY INSTEAD OF DOING ALL THE POLYGONS WE DO A SUBSET.
import time
import pandas
import json


def create_map(json_files, csv_files):
    """
    Map out_file_prefix to polygons, so we can find out which polygons are within or intersect a tumor region,
    and then be able to re-access the corresponding json and csv data.
    :param json_files:
    :param csv_files:
    :return:
    """
    rtn_dict = {}
    start_time = time.time()

    for n, jfile in enumerate(json_files):
        with open(jfile, 'r') as f:
            # Read JSON data into the json_dict variable
            json_dict = json.load(f)
            str = json_dict['out_file_prefix']
            imw = json_dict['image_width']
            imh = json_dict['image_height']
            cfile = csv_files[n]

            if str not in cfile:
                print('There should be 1 json file for 1 csv file.')
                exit(1)

            # Read CSV data into the dataframe variable
            df = pandas.read_csv(cfile)
            if df.empty:
                continue
            else:
                # out_file_prefix = Series
                # path_poly[str] = df['Polygon']
                path_poly = {}
                newList = []
                series_to_list = df['Polygon'].tolist()
                for s in series_to_list:
                    poly = string_to_polygon(s, imw, imh)
                    newList.append(poly)
                polyinfo = {"polygons": newList, "image_width": imw, "image_height": imh}
                path_poly[str] = polyinfo

            rtn_dict.update(path_poly)

        f.close()
        # rtn_dict.update(path_poly)

    elapsed_time = time.time() - start_time
    print('Runtime create_map: ')
    print(time.strftime("%H:%M:%S", time.gmtime(elapsed_time)))

    return rtn_dict


def string_to_polygon(s, imw, imh):
    print('dummy!')


# pre_poly_map = create_map(JSON_FILES, CSV_FILES)
# print('pre_poly_map', len(pre_poly_map))
#
# poly_within = get_polygons_within_tumors(pre_poly_map, tumor_poly_list)
# print('poly_within', len(poly_within))
