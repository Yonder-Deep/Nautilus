from pyproj import Transformer


def gps_to_espg_arctic(latitude, longitude):
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3575")
    new_latitude, new_longitude = transformer.transform(latitude, longitude)
    return new_latitude, new_longitude
