# This script retrieves the width and height of a whole-slide image by reading the image file and returning its dimensions.
import os
from pathlib import Path

from openslide import (OpenSlide)


def get_image_metadata():
    """
    Read slide and process
    :return:
    """
    p = Path(os.path.join(SLIDE_DIR, (CASE_ID + '.svs')))
    osr = OpenSlide(str(p))
    # props = osr.properties
    # props.__getitem__('openslide.level[0].width')
    # props.__getitem__('openslide.level[0].height')
    image_width = osr.dimensions[0]
    image_height = osr.dimensions[1]
    osr.close()
    return image_width, image_height


SLIDE_DIR = ''
CASE_ID = ''

# Get image width and height.
IMAGE_WIDTH, IMAGE_HEIGHT = get_image_metadata()
print(IMAGE_WIDTH, IMAGE_HEIGHT)
