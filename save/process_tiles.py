import math
import os
from pathlib import Path

from openslide import (OpenSlide)


def process_tiles(m_caseid):
    """
    Read slide and process
    :return:
    """
    tile_size = args["tile_size"]
    p = Path(os.path.join(SLIDE_DIR, (m_caseid + '.svs')))
    osr = OpenSlide(str(p))
    # props = osr.properties
    # props.__getitem__('openslide.level[0].width')
    # props.__getitem__('openslide.level[0].height')
    image_width = osr.dimensions[0]
    image_height = osr.dimensions[1]
    osr.close()

    tile_x = math.ceil(image_width / tile_size)
    tile_y = math.ceil(image_height / tile_size)
    print(tile_x, tile_y)

    # Calculate stuff...
    for i in range(tile_x):
        for j in range(tile_y):
            xpos = i * tile_size
            ypos = j * tile_size
            print(xpos, ypos)


def process_tile():
    print("process tile")


args = []
case_id = ''
SLIDE_DIR = ''

# Read slide & process
process_tiles(case_id)
