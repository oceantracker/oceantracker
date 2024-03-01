# wrappers for externally used libraries
import numpy as np
from pyproj import Proj, Transformer, CRS
from pyproj.aoi import AreaOfInterest
from pyproj.database import query_utm_crs_info
from math import floor

# integer values of EPSG at  https://spatialreference.org/

#   uses  (x,y) order,  so geographic are in (lon, lat) order
EPSG_WGS84 = 4326
EPSG_NZTM  = 2193

# set up class instances once to speed computation,
# xy=True will assume (lon,lat) input output
transformerNZTM_to_WGS84 = Transformer.from_crs(EPSG_NZTM , EPSG_WGS84, always_xy = True)
transformerWGS84_to_NZTM = Transformer.from_crs(EPSG_WGS84, EPSG_NZTM , always_xy = True)

#todo make latlong entry as columns in that order
def WGS84_to_NZTM(lon_lat, out=None):
    # (lng,lat ) to NZTM for numpy arays
    if out is None: out = np.full_like(lon_lat,0.)
    out[:,0],out[:,1] = transformerWGS84_to_NZTM.transform(lon_lat[:, 0], lon_lat[:, 1])
    return out

def NZTM_to_WGS84(xy, out=None):
    #  NZTM ( east, north)  to (lat, lng) for numpy arays
    if out is None: out = np.full_like(xy,np.nan)
    out[:,0],out[:,1] = transformerNZTM_to_WGS84.transform(xy[:,0], xy[:,1])

    # ensure longitude > 0
    sel= out[:,0] < 0
    out[sel,0] += 360.0
    return out

def get_tansformer(EPSG_in,EPSG_out):
    return Transformer.from_crs(EPSG_in, EPSG_out, always_xy=True)

def get_utm_epsg(lon_lat):
    # uses mean latlon to work out UTM zone
    lon_lat[lon_lat[:, 0] > 180., 0] -= 180

    utm_crs_list = query_utm_crs_info(
        datum_name="WGS 84",
        area_of_interest=AreaOfInterest(
            west_lon_degree= np.mean(lon_lat[:,0]),
            south_lat_degree=np.mean(lon_lat[:,1]),
            east_lon_degree=np.mean(lon_lat[:,0]),
            north_lat_degree=np.mean(lon_lat[:,1]),
        ),
    )
    return CRS.from_epsg(utm_crs_list[0].code)


def _get_WGS84_UTM_transformer(lon_lat):
    # (lat, lng) to NZTM for numpy arays
    # make row vector if needed
    epsg_utm=get_utm_epsg(lon_lat)
    T = get_tansformer(EPSG_WGS84,epsg_utm)
    return T, epsg_utm

def WGS84_to_UTM(lon_lat, out=None,in_lat_lon_order=False):
    # ll in (lat,lon) order

    if out is None: out = np.full_like(lon_lat,0.)
    if in_lat_lon_order:
        # swap input columns if inputs are as (lat, lon)  and not (lon,lat)
        lon_lat =  lon_lat[:,::-1]

    T, epsg_utm = _get_WGS84_UTM_transformer(lon_lat)
    out[:, 0], out[:, 1], = T.transform(lon_lat[:, 0], lon_lat[:, 1])
    return out

def convert_cords(xy, EPSG_in, EPSG_out):
    # interger values of EPSG at  https://spatialreference.org/
    T = get_tansformer(EPSG_in,EPSG_out)
    out = np.full_like(xy, 0.)
    out[:, 0], out[:, 1], = T.transform(xy[:, 0], xy[:, 1])
    return out

