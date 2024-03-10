import numpy as np


def calculate_direction(lat1, long1, lat2, long2):
    """Uses forward azimuth calculation to determine bearing"""
    lat1 = np.radians(lat1)
    long1 = np.radians(long1)
    lat2 = np.radians(lat2)
    long2 = np.radians(long2)

    dL = long2 - long1
    y = np.cos(lat2) * np.sin(dL)
    x = np.cos(lat1) * np.sin(lat2) - np.sin(lat1) * np.cos(lat2) * np.cos(dL)
    bearing = np.arctan2(y, x)
    direction = (np.degrees(bearing) + 360) % 360

    return direction


def calculate_distance(lat1, long1, lat2, long2):
    '''Uses haversine formula to determine distance'''
    R = 6371e3

    lat1 = np.radians(lat1)
    lat2 = np.radians(lat2)
    dLat = lat2 - lat1
    dLong = np.radians(long2 - long1)

    a = (np.sin(dLat / 2) * np.sin(dLat / 2)
         + np.cos(lat1) * np.cos(lat2) * np.sin(dLong / 2) * np.sin(dLong / 2))

    distance = 2 * R * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return distance


if __name__ == "__main__":
    coords = 40.714268, -74.005974, 48.856667, 2.350987
    direction, distance = calculate_direction(*coords), calculate_distance(*coords)
    print(direction, distance)
