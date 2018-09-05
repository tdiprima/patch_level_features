import os

import pandas


def get_polygon_data():
    """
    Get all the polygons.
    :return:
    """
    m_polygon_list = []

    try:
        for csv_dir1 in CSV_REL_PATHS:
            local = os.path.join(WORK_DIR, csv_dir1)
            if os.path.isdir(local) and len(os.listdir(local)) > 0:
                feature_filename_list = [f for f in os.listdir(local) if f.endswith('features.csv')]
                for ff in feature_filename_list:
                    # Read each file
                    data_frame = pandas.read_csv(os.path.join(local, ff))
                    df = pandas.DataFrame(data_frame)
                    if df.empty:
                        continue

                    val = data_frame['Polygon'].values[0]
                    ply = string_to_polygon(val)
                    m_polygon_list.append(ply)

    except Exception as ex:
        print('Error in get_polygon_data: ', ex)
        exit(1)

    return m_polygon_list


def string_to_polygon(thing):
    """
    DUMMY.
    :param thing:
    :return:
    """
    return thing


CSV_REL_PATHS = []
WORK_DIR = ''
tumor_poly_list = []
polygon_list = get_polygon_data()
print('polygon_list len: ', len(polygon_list))

within = 0
intersects = 0
disjoin = 0
for tumor_roi in tumor_poly_list:
    for polygon in polygon_list:
        if polygon.within(tumor_roi):
            within += 1
        if polygon.intersects(tumor_roi):
            intersects += 1
        if polygon.disjoint(tumor_roi):
            disjoin += 1
print('within', within)
print('intersects', intersects)
print('disjoin', disjoin)
