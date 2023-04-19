# This code converts a list of coordinate points into a list of polygons.
def coordinates_to_polygons(coordinates_list):
    """
    Clean up and convert to something we can use.
    :param coordinates_list:
    :return:
    """
    m_poly_list = []
    points_list = []
    try:
        # roll through our list of [x,y]
        for m_point in coordinates_list:
            # convert the point coordinates to Points
            m_point = Point(m_point[0], m_point[1])
            points_list.append(m_point)
        # create a Polygon
        m = MultiPoint(points_list)
        m_polygon = Polygon(m)
        # append to return-list
        m_poly_list.append(m_polygon)
    except Exception as ex:
        print('Error in convert_to_polygons', ex)
        exit(1)

    # Return list of polygons
    return m_poly_list
