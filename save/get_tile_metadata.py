# This script reads JSON files in a specified directory tree, extracts metadata such as tile width, height, and
# minimum x,y points, and returns a list of unique tile minimum points and the tile width and height.
import json
import os

CSV_REL_PATHS = []


def get_tile_metadata(local_folder):
    """
    Get tile w, h
    Get list of tile upper x, y from JSON files.
    :param local_folder:
    :return:
    """
    m_tlw = str(0)  # tile width
    m_tlh = str(0)  # tile height
    once = 0

    tile_min_point_list = []

    # Roll through the folders and JSON files for this case_id.
    for csv_dir1 in CSV_REL_PATHS:
        local = os.path.join(local_folder, csv_dir1)

        if os.path.isdir(local) and len(os.listdir(local)) > 0:
            # Get list of JSON files we have to read
            json_filename_list = [f for f in os.listdir(local) if f.endswith('.json')]
            for json_filename in json_filename_list:
                # Read each JSON file
                with open(os.path.join(local, json_filename)) as f:
                    # f = _io.TextIOWrapper
                    data = json.load(f)

                    if once == 0:
                        once = 1
                        m_tlw = data["tile_width"]
                        m_tlh = data["tile_height"]

                    if m_tlw != data["tile_width"] or m_tlh != data["tile_height"]:
                        print("DIFF TILE W/H")
                        print(m_tlw, m_tlh)
                        exit(0)

                    m_tlw = data["tile_width"]
                    m_tlh = data["tile_height"]

                    # print('data', data)
                    # Get point
                    # point [67584, 45056]
                    # data[analysis_id]

                    tile_minx = data["tile_minx"]
                    tile_miny = data["tile_miny"]
                    m_point = [tile_minx, tile_miny]
                    tile_min_point_list.append(m_point)

    # tmp_set {(67584, 45056)} etc.
    tmp_set = set(map(tuple, tile_min_point_list))
    # for n in tmp_set:
    #     print(n)
    # convert to {[67584, 45056]}
    unique_tile_min_point_list = map(list, tmp_set)
    return m_tlw, m_tlh, unique_tile_min_point_list

# For processing slide later on
# tile_width, tile_height, tile_minxy_list = get_tile_metadata(WORK_DIR)
