import folium
import pyproj

x1, y1 = 79.827878, 14.516178

transformer = pyproj.Transformer.from_crs("EPSG:3857", "EPSG:3575")
x2, y2 = transformer.transform(y1, x1)
print(x2)
print(y2)

# Define the URL for the custom tile provider
tile_url = "http://tiles.arcticconnect.ca/osm_3575/{z}/{x}/{y}.png"

#tiles=tile_url, attr="toner-bcg"

# Create a Folium Map object using the reprojected center coordinates
m = folium.Map(tiles=tile_url, attr="toner-bcg")
m.fit_bounds(m.get_bounds())

#tiles=tile_url, attr="toner-bcg", 


folium.Marker(
      location=[50,50],
      popup=str(x2) + "," + str(y2)
   ).add_to(m)

   
m.save("footprint.html")