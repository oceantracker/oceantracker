from  copy import deepcopy, copy
import numpy as np
import json
from os import path
from datetime import datetime,date, timedelta
import numba.core.types

def write_JSON(file_name,d, indent=4):
    # aviod changing given file name
    if '.json' in file_name.lower():
        fn = file_name
    else:
        fn=file_name+'.json'
    try:
        with open(fn, mode='w') as fp:
            json.dump(d, fp, cls=MyEncoder, indent=indent)

    except Exception as e:
        print('Error>>  Failed to write json file ="' + file_name +'"')
        raise(e)
    pass

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
    def __int__(self):
        super().__int__(allow_nan=False)

    def default(self, obj):
        val =  deepcopy(obj)
        try :

            # first numpy types
            if isinstance(obj, np.ndarray):
                if np.all(np.isfinite(obj)):
                    if obj.dtype == np.datetime64:
                        return  str(obj)
                    elif obj.dtype in [np.bool_,bool]:
                        return   obj.astype(np.int8).tolist()
                    else:
                        return   obj.tolist()
                else:
                    # fire fox cant read nan in json so make an object array, with nan as none
                    sel = ~np.isfinite(obj)
                    val[sel]= 9.99999e32
                    return  val.tolist()

            elif isinstance(obj,(np.int8, np.int16, np.int32,np.int64)):
                # make single numpy int values
                return  int(obj)
            elif type(obj) in (np.float16, np.float32, np.float64):
                # make single numpy float values
                if not np.isfinite(obj):
                    return  None
                else:
                    return  float(obj)
            elif type(obj) == float:
                if not np.isfinite(obj):
                    return  None
                else:
                    return  float(obj)

            elif  type(obj) in [np.bool_,bool]:
                # make single numpy int values
                return  int(obj)
            # date/time strings
            elif isinstance(obj, (datetime, date)):
                return  obj.isoformat()

            elif isinstance(obj,type):
                return  obj.__name__

            elif type(obj) == np.datetime64:
                return  str(obj)

            elif type(obj) == np.timedelta64:
                return  str(obj.astype(timedelta)) # timedelta has better formating

            elif isinstance(obj,np.dtype):
                return  str(obj)
            elif type(obj) == timedelta:
                return  str(obj)

            elif np.isnan(obj) or not np.isfinite(obj):
                return  None
            else:
                return str(val)

            return super().default(self, val)

        except Exception as e:
            #print(str(e))
            print(' warning  basic_util- oceantracker catch JSON encode error- object type ' + str(type(obj)) + ' value=' + str(obj))
            return f'Bad json value, not json decodable type {str(type(obj))}  values= {str(obj)}'

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
    features = [F_base]
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