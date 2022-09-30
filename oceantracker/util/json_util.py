from  copy import deepcopy, copy
import numpy as np
import json
from os import path
from datetime import datetime,date


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

    def default(self, obj):

        try :
            # first numpy types
            if isinstance(obj, np.ndarray):
                if np.all(np.isfinite(obj)):
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

            elif isinstance(obj,(float, np.float32, np.float64)) :
                # make single numpy float values
                val =float(obj)  if np.isfinite(obj) else None
                return val

            elif isinstance(obj, (datetime, date)):
                return obj.isoformat()

            elif isinstance(obj,type):
                return obj.__name__

            elif isinstance(obj,np.dtype):
                return str(obj)

            return json.JSONEncoder.default(self, obj)

        except:
            raise ValueError(' basic_util- catch JSON encode error- object type ' + str(type(obj))+ ' as ' + str(obj))
            return 'BadValue'