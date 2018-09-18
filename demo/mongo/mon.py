from pymongo import MongoClient

client = MongoClient('mongodb://quip3.bmi.stonybrook.edu:27017/')
db = client.quip_comp
bridge = db.patch_level_features
me = db.test_features_td

arr = ['case_id', 'patch_size', 'patch_min_x_pixel', 'patch_min_y_pixel', 'patch_polygon_area',
       'percent_nuclear_material', 'grayscale_patch_mean', 'grayscale_patch_std',
       'hematoxylin_patch_mean', 'hematoxylin_patch_std', 'flatness_segment_mean', 'flatness_segment_std',
       'perimeter_segment_mean', 'perimeter_segment_std',
       'circularity_segment_mean', 'circularity_segment_std', 'r_GradientMean_segment_mean',
       'r_GradientMean_segment_std', 'b_GradientMean_segment_mean',
       'b_GradientMean_segment_std', 'r_cytoIntensityMean_segment_mean', 'r_cytoIntensityMean_segment_std',
       'b_cytoIntensityMean_segment_mean', 'b_cytoIntensityMean_segment_std',
       'elongation_segment_mean', 'elongation_segment_std']


def is_number(s):
    try:
        float(s)  # for int, long and float
    except ValueError:
        try:
            complex(s)  # for complex
        except ValueError:
            return False

    return True


header = ''
for thing in arr:
    header += thing + '\t'

f = open("demofile.txt", "a")
f.write(header)

for doc in bridge.find({'case_id': 'PC_058_0_1'}):
    x = doc['patch_min_x_pixel']
    y = doc['patch_min_y_pixel']
    items = me.find_one({'patch_min_x_pixel': x, 'patch_min_y_pixel': y})
    if items is not None:
        row = ''
        for x in range(5, len(arr)):
            name = arr[x]
            try:
                val1 = doc[name]
            except KeyError:
                val1 = doc[name.capitalize()]
            val2 = items[name]
            if is_number(val1) and is_number(val2):
                myFloat = abs(val1 - val2)
                # myFloat = round(float(myFloat), 7)
                if x == len(arr):
                    row += str(myFloat)
                else:
                    row += str(myFloat) + '\t'

        f.write(row)

f.close()
