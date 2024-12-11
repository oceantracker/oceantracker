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

_transformerNZTM_to_WGS84 = Transformer.from_crs(EPSG_NZTM , EPSG_WGS84, always_xy = True)
_transformerWGS84_to_NZTM = Transformer.from_crs(EPSG_WGS84, EPSG_NZTM , always_xy = True)


def WGS84_to_NZTM(lon_lat, out=None):
    # (lng,lat ) to NZTM for numpy arays
    if out is None: out = np.full_like(lon_lat,0.)
    out[:,0],out[:,1] = _transformerWGS84_to_NZTM.transform(lon_lat[:, 0], lon_lat[:, 1])
    return out

def NZTM_to_WGS84(xy, out=None):
    #  NZTM ( east, north)  to (lat, lng) for numpy arays
    if out is None: out = np.full_like(xy,np.nan)
    out[:,0],out[:,1] = _transformerNZTM_to_WGS84.transform(xy[:,0], xy[:,1])

    # ensure longitude > 0
    sel= out[:,0] < 0
    out[sel,0] += 360.0
    return out

def get_tansformer(EPSG_in,EPSG_out):
    return Transformer.from_crs(EPSG_in, EPSG_out, always_xy=True)

def get_utm_epsg(lon_lat):
    # uses mean latlon to work out UTM zone
    lon_lat[lon_lat[:, 0] > 180., 0] -= 360

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


def fix_any_spanning180east(lon_lat,single_cord=False, msg_logger=None, caller=None, crumbs=None):
    # check longitudes spanning 180, ie jumps from 179 E to -179 East
    if single_cord: lon_lat = lon_lat[np.newaxis,:]
    bounds= [lon_lat[:,0].min(), lon_lat[:,0].max()]
    if abs(bounds[1] - bounds[0]) > 180:
        # spanning 180 deg east
        sel = lon_lat[:, 0] < 0
        lon_lat[sel,:] += 360.
        msg_logger.msg( f'Hydro-model coordinates are geographic and span 180 degrees east, converting to 0-360 degrees',
                        note=True, caller =caller,crumbs=crumbs )
    if single_cord: lon_lat = lon_lat[0]
    return lon_lat

def get_deg_per_meter(lon_lat, single_cord=False):
    dx = 1. / 111000.  # deg per m of latitude, rows of lon_lat are multiple locations
    if single_cord: lon_lat = lon_lat[np.newaxis, :]
    out = np.full_like(lon_lat,0., dtype =lon_lat.dtype)

    out[:, 0] = dx * np.cos(np.deg2rad(lon_lat[:, 1]))
    out[:, 1]= dx
    if single_cord: out = out[0]
    return  out

def rectangle_area_meters_sq(xll,yll, xur, yur, is_geographic=False):
    # calculate area of "small" retangle in meters squred, for bth m's and geographic coorindates
    # given coords of lower left and upper right
    if is_geographic:
        dxy = get_deg_per_meter(np.asarray([xll,.5*(yll+yur)]), single_cord=True)
        return ((xur-xll)/dxy[0])*((yur-yll)/dxy[1])
    else:
        return (xur - xll)*(yur-yll)
