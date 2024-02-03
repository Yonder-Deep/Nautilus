from pyproj import Geod

'''
Using a library such as pyproj has multiple benefits:

1) simple to use/less error prone
2) more accurate, WGS84 standard used in GPS for example
3) more features, methods such as calculating coordinates based
on heading and distance, and distance between points on a line
'''

geod = Geod(ellps='WGS84')

lat1, long1, lat2, long2 = 40.714268, -74.005974, 48.856667, 2.350987
initial_bearing, _, distance = geod.inv(long1, lat1, long2, lat2)

print(initial_bearing, distance)
