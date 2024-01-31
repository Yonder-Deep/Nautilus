from numpy import arctan2, sin, cos, degrees


def calculate_direction(lat1, long1, lat2, long2):
    """Uses forward azimuth calculation to determine bearing (can also use haversine)"""
    direction = 0
    dL = long2 - long1
    X = cos(lat2) * sin(dL)
    Y = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(dL)
    bearing = arctan2(X, Y)
    direction = (degrees(bearing) + 360) % 360
    return direction


if __name__ == "__main__":
    direction = calculate_direction(32.883233, -117.235239, 32.883404, -117.235400)
    print(direction)
