"""
Refactor Tile Processor
This file processes large slide images by dividing them into 512x512 pixel tiles based on metadata inputs,
saves each tile as a PNG file, and optionally checks for geometric features within each tile.
TODO: Need svs slide
"""
import json

import openslide
from shapely.geometry import Polygon


def load_metadata(metadata_path):
    """Load metadata from a JSON file."""
    with open(metadata_path, 'r') as f:
        return json.load(f)


def generate_tile_bbox(tile_size, x, y, minx, miny):
    """Generate the bounding box for a tile."""
    minx_tile = minx + (x * tile_size)
    miny_tile = miny + (y * tile_size)
    maxx_tile = minx_tile + tile_size
    maxy_tile = miny_tile + tile_size
    return Polygon([
        (minx_tile, miny_tile),
        (maxx_tile, miny_tile),
        (maxx_tile, maxy_tile),
        (minx_tile, maxy_tile)
    ])


def process_tiles(slide, metadata, tile_size):
    """Process tiles for the given slide and metadata."""
    width = metadata['patch_width']
    height = metadata['patch_height']
    minx = metadata['patch_minx']
    miny = metadata['patch_miny']

    cols = int(width / tile_size)
    rows = int(height / tile_size)

    count = 0
    for x in range(1, cols + 1):
        for y in range(1, rows + 1):
            count += 1
            bbox = generate_tile_bbox(tile_size, x, y, minx, miny)

            # Extract the tile image
            tile = slide.read_region((int(bbox.bounds[0]), int(bbox.bounds[1])), 0, (tile_size, tile_size))
            tile.save(f'tile{count}.png', "PNG")

            # TODO: Optionally add feature checks or other processing here
            # process_tile_features(bbox)


def process_tile_features(bbox):
    """Placeholder for processing features within the tile."""
    # Example logic for checking features within the bounding box
    # Features would be read or processed here
    pass


def main():
    """Main function to execute the tile processing."""
    metadata_path = 'x63488_y49152-algmeta.json'
    slide_path = 'PC_051_0_1.svs'

    # Load metadata and slide
    metadata = load_metadata(metadata_path)
    slide = openslide.OpenSlide(slide_path)

    # Process the tiles
    tile_size = 512
    process_tiles(slide, metadata, tile_size)


if __name__ == "__main__":
    main()
