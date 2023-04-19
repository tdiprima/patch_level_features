import json
import pandas
from planar import BoundingBox, Vec2
import openslide
from shapely.geometry import Polygon, Point, MultiPoint

tile_size = 512

with open('x63488_y49152-algmeta.json', 'r') as f:
    dict1 = json.load(f)

    width = dict1['patch_width']
    height = dict1['patch_height']
    minx = dict1['patch_minx']
    miny = dict1['patch_miny']

    cols = width / tile_size
    rows = height / tile_size

    data_complete = {}
    slide = openslide.OpenSlide('/data1/tdiprima/dataset/PC_051_0_1/PC_051_0_1.svs')

    count = 0
    for x in range(1, (int(cols) + 1)):
        for y in range(1, (int(rows) + 1)):
            data = {}
            count += 1
            # minx = minx + (x * tile_size)
            # miny = miny + (y * tile_size)
            minx = x * tile_size
            miny = y * tile_size
            minx = minx + dict1['patch_minx']
            miny = miny + dict1['patch_miny']
            maxx = minx + tile_size
            maxy = miny + tile_size
            # print((minx, miny), (maxx, miny), (maxx, maxy), (minx, maxy))
            bbox = BoundingBox([(minx, miny), (maxx, miny), (maxx, maxy), (minx, maxy)])
            tile = slide.read_region((minx, miny), 0, (tile_size, tile_size))
            tile.save('tile' + str(count) + '.png', "png")

            # print(bbox)
            df = pandas.read_csv('x63488_y49152-features.csv')
            row_list = []
            df2 = pandas.DataFrame()
            for index, row in df.iterrows():
                poly_data = row['Polygon']
                tmp_str = str(poly_data)
                tmp_str = tmp_str.replace('[', '')
                tmp_str = tmp_str.replace(']', '')
                split_str = tmp_str.split(':')
                # Get list of points
                for i in range(0, len(split_str) - 1, 2):
                    a = float(split_str[i])
                    b = float(split_str[i + 1])
                    # point = [a, b]
                    point = Vec2(a, b)
                    if bbox.contains_point(point):
                        # do something and break
                        row_list.append(row)
                        df2.append(row)
                        print(bbox)
                        break
                # print('row_list', row_list)
            # data_complete.update({data[count]: {'bbox': bbox, 'row_list': row_list}})
            if row_list:
                data[count] = {'bbox': bbox, 'row_list': row_list}
                data_complete.update(data)

# print(data_complete)
# df2['Perimeter'].mean()
for k, v in data_complete.items():
    print(k)
