"""
This script demonstrates how to check if a point lies inside a polygon and whether two lines
intersect or touch, using the Shapely library for geometric operations.
https://automating-gis-processes.github.io/2017/lessons/L3/point-in-polygon.html
"""

from shapely.geometry import Point, Polygon
from shapely.geometry import LineString, MultiLineString


def point_inside_poly(point, polygon):
    # Check if p1 is within the polygon using the within function
    print("within: ", point.within(polygon))

    # REVERSE
    # Does polygon contain p1?
    print("contains: ", polygon.contains(point))


def intersect(line_a, line_b):
    print("lines a & b intersect?", line_a.intersects(line_b))
    print("lines a & b touch?", line_a.touches(line_b))
    print("line a touches itself?", line_a.touches(line_a))
    print("line a intersect itself?", line_a.intersects(line_a))


# Create Point objects
p1 = Point(24.952242, 60.1696017)
p2 = Point(24.976567, 60.1612500)

# Create a Polygon
coords = [(24.950899, 60.169158), (24.953492, 60.169158), (24.953510, 60.170104), (24.950958, 60.169990)]
poly = Polygon(coords)

point_inside_poly(p1, poly)
point_inside_poly(p2, poly)

# Create two lines
a = LineString([(0, 0), (1, 1)])
b = LineString([(1, 1), (0, 2)])
intersect(a, b)
