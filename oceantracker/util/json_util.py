from  copy import deepcopy, copy
import numpy as np
import json
from os import path
from datetime import datetime,date, timedelta


def write_JSON(file_name,d, indent=4):
    # aviod changing given file name
    if '.json' in file_name.lower():
        fn = file_name
    else:
        fn=file_name+'.json'
    try:
        with open(fn, 'w') as fp:
            json.dump(d, fp, cls=MyEncoder, indent=indent)

    except Exception as e:
        print('Error>>  Failed to write json file ="' + file_name +'"')
        raise(e)


def read_JSON(file_name):
    # avoid changing given file name
    file_name= path.normpath(file_name)
    if file_name is None or not path.isfile(file_name):
        raise Exception('Cannot find json file "' + file_name + '"  ')

    try:
        with open(file_name, 'r') as fp:
            d=json.load(fp)
    except Exception as e:
        print( 'Oeantracker: Error>> Could not read json file, may not be a valid json' + file_name)
        raise(e)

    return d


#Store as JSON a numpy.ndarray or any nested-list composition.
class MyEncoder(json.JSONEncoder):
    def _custom_preprocess_dict(self, val):

        if isinstance(val,(float,np.float64,np.float32)) and not np.isfinite(val):
            return 'not finite'
        if isinstance(val, datetime):
            return  val.isoformat()
        else:
           return val

    def encode_notused(self, d):
        if isinstance(d,dict):
            for key in d.keys():
                d[key]= self._custom_preprocess_dict(d[key])

        return super().encode(d)

    def default(self, obj):

        try :
            # first numpy types
            if isinstance(obj, np.ndarray):
                if np.all(np.isfinite(obj)):
                    if obj.dtype == np.datetime64:
                        str(obj)
                    else:
                        return  obj.tolist()
                else:
                    # fire fox cant read nan in json so make an object array, with nan as none
                    r= np.full_like(obj, None, dtype=object)
                    sel = np.isfinite(obj)
                    r[sel]= obj[sel]
                    return r.tolist()

            elif isinstance(obj,(np.int8, np.int16, np.int32,np.int64)):
                # make single numpy int values
                return int(obj)


            # date/time strings
            elif isinstance(obj, (datetime, date)):
                return obj.isoformat()

            elif isinstance(obj,type):
                return obj.__name__

            elif type(obj) == np.datetime64:
                return str(obj)

            elif isinstance(obj, (np.bool_,np.bool)):
                return bool(obj)

            elif type(obj) == np.timedelta64:
                return str(obj.astype(timedelta)) # timedelta has better formating

            elif isinstance(obj,np.dtype):
                return str(obj)
            elif type(obj) == timedelta:
                return str(obj)

            elif np.isnan(obj) or not np.isfinite(obj) :
                return None

            return json.JSONEncoder.default(self, obj)

        except:
            raise ValueError(' basic_util- catch JSON encode error- object type ' + str(type(obj))+ ' as ' + str(obj))
            return 'BadValue'

# geojson polygons
#todo make reader to/from internal polygon format
geojson_polygon_template ={
   "type": "Feature",
   "geometry":  "Polygon",
        "coordinates": None ,#[] N by 2 list

        "properties": {
                "polygon_group": None,  # use for tagging domain and islands?
                'name' : None, # name of polygo assigrn by user or code
                'user_polygonID': None,
                'user_polygon_name' : None,

        }
}


geometries_template = {
'type': 'FeatureCollection',
'features': None,
}

def writegeojson(f,polygonlist):
    features = [F0]
    for i in map['islands']:
        f = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": i['points']
            },
            "properties": {
                "boundary_type": "island",
            }
        }
        features.append(f)
    #with open('data\oceanum_grid_outline.geojson','w') as f:
    #    geojson.dump(geometries,f)