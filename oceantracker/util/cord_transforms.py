# wrappers for externally used libraries
import numpy as np
from pyproj import Proj, Transformer, CRS
from pyproj.aoi import AreaOfInterest
from pyproj.database import query_utm_crs_info
from math import floor

# cord transforms from remy
#   uses  (x,y) order,  so geographic are in (lon, lat) order
ID_WGS84 = 4326
ID_NZTM  = 2193

# set up class instances once to speed computation,
# xy=True will assume (lon,lat) input output
transformerNZTM_to_WGS84 = Transformer.from_crs(ID_NZTM , ID_WGS84, always_xy = True)
transformerWGS84_to_NZTM = Transformer.from_crs(ID_WGS84, ID_NZTM , always_xy = True)

#todo make latlong entry as columns in that order
def WGS84_to_NZTM(lon_lat, out=None):
    # (lng,lat ) to NZTM for numpy arays
    if out is None: out = np.full_like(lon_lat,0.)
    out[:,0],out[:,1] = transformerWGS84_to_NZTM.transform(lon_lat[:, 0], lon_lat[:, 1])
    return out

def NZTM_to_WGS84(xy, out=None):
    #  NZTM ( east, north)  to (lat, lng) for numpy arays
    if out is None: out = np.full_like(xy)
    out[:,0],out[:,1] = transformerNZTM_to_WGS84.transform(xy[:,0], xy[:,1])

    # ensure longitude > 0
    sel= out[:,0] < 0
    out[sel,0] += 360.0
    return out

def _get_WGS84_UTM_transformer(lon_lat):
    # (lat, lng) to NZTM for numpy arays
    # make row vector if needed
    lon_lat[lon_lat[:,0]> 180., 0] -= 180

    utm_crs_list = query_utm_crs_info(
        datum_name="WGS 84",
        area_of_interest=AreaOfInterest(
            west_lon_degree= np.mean(lon_lat[:,0]),
            south_lat_degree=np.mean(lon_lat[:,1]),
            east_lon_degree=np.mean(lon_lat[:,0]),
            north_lat_degree=np.mean(lon_lat[:,1]),
        ),
    )
    utm_crs = CRS.from_epsg(utm_crs_list[0].code)
    T = Transformer.from_crs(ID_WGS84, utm_crs, always_xy = True)
    return T

def WGS84_to_UTM(lon_lat, out=None):
    # ll in (lat,lon) order
    # uses mean latlon to work out zone
    if out is None: out = np.full_like(lon_lat,0.)
    T = _get_WGS84_UTM_transformer(lon_lat)

    out[:, 0], out[:, 1], = T.transform(lon_lat[:, 0], lon_lat[:, 1])
    return out, T
