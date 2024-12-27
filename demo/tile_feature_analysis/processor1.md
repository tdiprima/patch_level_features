## Tile Processor

The file contains code for processing large whole-slide images by dividing them into tiles and checking if specific geometric features intersect with those tiles. It handles metadata and feature data, and uses geometric libraries like `planar` (which will need to be replaced with `shapely`).

Extract the nested loop structure and work on reducing its depth while incorporating `shapely`. Provide comments and make it modular for better readability and maintenance.

The code snippet involves reading metadata from a JSON file, creating tiles from an image, and checking if geometric features are within those tiles. The nested loops iterate over a grid to generate the tiles, creating bounding boxes and performing feature checks.

If you intend to take specific actions upon finding features (e.g., saving metadata, flagging tiles, or performing additional processing), you’ll need to implement that logic in `process_tile_features`.

### Observations:
1. **Nested Loops**:
   - The outer loop iterates over columns.
   - The inner loop iterates over rows.
2. **Geometry Processing**:
   - Bounding boxes are created using `planar` (to be replaced by `shapely`).
3. **Tile Processing**:
   - Tiles are read from the image and saved as PNG files.

### Approach:
1. Replace `BoundingBox` from `planar` with `shapely.geometry.Polygon`.
2. Flatten the nested loops using helper functions for better readability.
3. Optimize tile creation and feature checking to reduce redundancy.

Refactored the code to reduce nesting and replaced the use of `planar` with `shapely`. Key changes include:

1. **Modularity**: 
   - Functions for loading metadata, generating tile bounding boxes, and processing tiles.
   - Each function has a clear purpose.

2. **Shapely Integration**:
   - Used `shapely.geometry.Polygon` to represent bounding boxes.

3. **Reduced Nesting**:
   - Logic inside the nested loops was moved to helper functions (`generate_tile_bbox`, `process_tile_features`).

<br>
