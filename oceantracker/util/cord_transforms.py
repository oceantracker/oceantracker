# wrappers for externally used libraries
import numpy as np
from pyproj import Proj, Transformer, CRS
from pyproj.aoi import AreaOfInterest
from pyproj.database import query_utm_crs_info
from math import floor

# cord transforms from remy

ID_WGS84 = 4326
ID_NZTM  = 2193

# set up class instances once to speed computation
transformerNZTM_to_WGS84 = Transformer.from_crs(ID_NZTM , ID_WGS84)
transformerWGS84_to_NZTM = Transformer.from_crs(ID_WGS84, ID_NZTM )


def WGS84_to_NZTM(ll):
    # (lat, lng) to NZTM for numpy arays
    # make row vector if needed
    if ll.ndim == 1: ll=ll.reshape((1,-1))

    xy= np.full(ll.shape,np.nan)
    xy[:,1], xy[:,0]= transformerWGS84_to_NZTM.transform(ll[:,0], ll[:,1])

    return xy

def NZTM_to_WGS84(xy):
    #  NZTM ( east, north)  to (lat, lng) for numpy arays
    # make row vector if needed
    if xy.ndim == 1:xy=xy.reshape((1,-1))

    ll= np.full(xy.shape,np.nan)
    ll[:,0], ll[:,1]= transformerNZTM_to_WGS84.transform(xy[:,1], xy[:,0]) # not sure why xy are swapped here but it works

    # ensure longitude > 0
    sel= ll[:,1] < 0
    ll[sel, 1]= ll[sel, 1]+360.0
    return ll


def get_WGS84_UTM_transformer(ll):
    # (lat, lng) to NZTM for numpy arays
    # make row vector if needed

    utm_crs_list = query_utm_crs_info(
        datum_name="WGS 84",
        area_of_interest=AreaOfInterest(
            west_lon_degree= np.mean(ll[:,0]),
            south_lat_degree=np.mean(ll[:,1]),
            east_lon_degree=np.mean(ll[:,0]),
            north_lat_degree=np.mean(ll[:,1]),
        ),
    )
    utm_crs = CRS.from_epsg(utm_crs_list[0].code)
    T = Transformer.from_crs(ID_WGS84, utm_crs)
    return T

def WGS84_to_UTM(ll):
    # uses mean latlong to work out zone
    T = get_WGS84_UTM_transformer(ll)
    xy = np.full(ll.shape, np.nan)
    xy[:, 0], xy[:, 1] = T.transform(ll[:, 1], ll[:, 0])
    return xy
