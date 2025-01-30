import io
from urllib.request import urlopen, Request
from PIL import Image
import cartopy.feature as cf
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import cartopy.io.img_tiles as cimgt


def image_spoof(self, tile):
    '''this function reformats web requests from OSM for cartopy
    Heavily based on code by Joshua Hrisko at:
        https://makersportal.com/blog/2020/4/24/geographic-visualizations-in-python-with-cartopy'''

    url = self._image_url(tile)                # get the url of the street map API
    req = Request(url)                         # start request
    req.add_header('User-agent', 'Anaconda 3')  # add user agent to request
    fh = urlopen(req)
    im_data = io.BytesIO(fh.read())            # get image
    fh.close()                                 # close url
    img = Image.open(im_data)                  # open image with PIL
    img = img.convert(self.desired_tile_form)  # set image format
    return img, self.tileextent(tile), 'lower'  # reformat for cartopy


crs = ccrs.PlateCarree()
#crs = ccrs.Geodetic()

# Now we will create axes object having specific projection
plt.figure(dpi=150)

cimgt.QuadtreeTiles.get_image = image_spoof  # reformat web request for street map spoofing
img = cimgt.QuadtreeTiles()  # spoofed, downloaded street map

projection = ccrs.NorthPolarStereo(central_longitude=15)
#projection = img.crs

ax = plt.axes(projection=projection, frameon=True)
tile_image = ax.add_image(img, 3)

# Draw gridlines in degrees over Mercator map
gl = ax.gridlines(crs=crs, draw_labels=True,
                  linewidth=.6, color='gray', alpha=0.5, linestyle='-.')
gl.xlabel_style = {"size": 7}
gl.ylabel_style = {"size": 7}

# To plot borders and coastlines, we can use cartopy feature
ax.add_feature(cf.COASTLINE.with_scale("50m"), lw=0.5)
ax.add_feature(cf.BORDERS.with_scale("50m"), lw=0.3)

# Now, we will specify extent of our map in minimum/maximum longitude/latitude
# Note that these values are specified in degrees of longitude and degrees of latitude
# However, we can specify them in any crs that we want, but we need to provide appropriate
# crs argument in ax.set_extent
lon_min = 5
lon_max = 30
lat_min = 75
lat_max = 85

# crs is PlateCarree -> we are explicitly telling axes, that we are creating bounds that are in degrees
ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=crs)

longs = [16.482034, 20.776085]
lats = [80.072230, 81.192673]

plt.plot(longs, lats, color='blue', linewidth=2, marker='o', transform=crs)
#plt.plot(15.776085, 80.192673, color='blue', linewidth=2, marker='o', transform=crs)


plt.show()