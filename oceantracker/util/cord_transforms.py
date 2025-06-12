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


def fix_any_spanning180east(lon_lat, msg_logger=None, caller=None, crumbs=None):
    # check longitudes spanning 180, ie jumps from 179 E to -179 East
    # and adjust in place
    if lon_lat.ndim < 2:
        msg_logger.msg(f'fix_any_spanning180east: lon_lat must be 2D (N,2 or 3)',
                       fatal_error=True, caller=caller, crumbs=crumbs)

    bounds= [lon_lat[:,0].min(), lon_lat[:,0].max()]
    if abs(bounds[1] - bounds[0]) > 180:
        # spanning 180 deg east
        sel = lon_lat[:, 0] < 0
        lon_lat[sel,0] += 360.
        msg_logger.msg( f'Hydro-model coordinates are geographic and span 180 degrees east, converting to 0-360 degrees',
                        note=True, caller =caller,crumbs=crumbs )


def get_degrees_per_meter(lat, as_vector=False):
    # rough lon lat in deg,
    # todo full jacobian from pytrans and finite differences and both lat, long

    dx = 1. / 111000.  # deg per m of latitude, rows of lon_lat are multiple locations

    dpm_lon = dx * np.cos(np.deg2rad(lat))
    dpm_lat = dx *np.ones(lat.shape)

    if as_vector:
        return np.stack((dpm_lon,dpm_lat),axis = lat.ndim)  # merge on last dim of lat
    else:
        return dpm_lon,dpm_lat

def local_grid_deg_to_meters(lon,lat, lon_origin, lat_origin, as_vector=False):
    # get coords in meters from small local grid with given origin(s)

    d_per_m_lon,d_per_m_lat= get_degrees_per_meter(lat)

    x = (lon-lon_origin)/d_per_m_lon
    y = (lat - lat_origin) / d_per_m_lat
    if as_vector:
        return np.stack((x, y), axis=x.ndim)  # merge on last dim of lat
    else:
        return x, y
def local_meters_grid_to_deg(x,y, lon_origin, lat_origin, as_vector=False):
    # get coords in (lon,lat) from small local grid with (x,y) meters offsets from given origin(s)

    d_per_m_lon,d_per_m_lat= get_degrees_per_meter(lat_origin)

    lon = lon_origin + d_per_m_lon * x
    lat = lat_origin + d_per_m_lat * y

    if as_vector:
        return np.stack((lon, lat), axis=x.ndim)  # merge on last dim of lat
    else:
        return lon, lat
