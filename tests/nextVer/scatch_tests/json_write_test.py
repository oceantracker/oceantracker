import numpy as np
from oceantracker.util import json_util
import json
from datetime import datetime
from  copy import deepcopy
class CustomEncoder(json.JSONEncoder):
    def _custom_preprocess(self,val):

        if isinstance(val, float):
            return  str(val) +'>>>h'
        if isinstance(val, datetime):
            return val.isoformat()
        else:
            val

    def encode(self, d):
        print('obj',d)
        if isinstance(d, dict):
            for key in d.keys():
                d[key] = self._custom_preprocess(d[key])
            return d
        else:
            return super().encode(d)



data={"b":3, "a":np.inf,"x": 1.,   "created_at": datetime.now()}
print(data)

print('A',json.dumps(deepcopy(data), cls=CustomEncoder))

print('B',json.dumps(deepcopy(data), cls=json_util.MyEncoder))