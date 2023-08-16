import numpy as np

from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
import fiona
from os import  path


class ReadCoordinates(ParameterBaseClass):
    modes=['polygon','points']
    def __init__(self):
        super().__init__()
        self.add_default_params({'file_name' :  PVC(None, str, is_required=True, doc_str=' shape or geojson file name readble by "fiona" packakge, must include path if not in dir with code')
                                 })
        # sets of all polygons
        self.user_polygons=[]
        self.user_points = []
        self.user_points_lines=[]

    def initial_setup(self):
        si= self.shared_info
        info = self.info
        ml= si.msg_logger
        params = self.params

        # readd file
        if not path.isfile(params['file_name']):
            ml.msg(f'cannot file {params["file_name"]}' ,
                   hint='Check path and name',
                   fatal_error= True, exit_now= True,
                   crumbs='Pre processing > ReadCoordinates')
        try:
            d= fiona.open(params['file_name'])
        except Exception as e:
            ml.msg(f'cannot read file {params["file_name"]} ', hint='File tyype not recognised by "fiona" module',
                   fatal_error=True, exit_now=True, crumbs='Pre processing > ReadCoordinates')

        for item in d:
            g = item['geometry']
            xy = np.asarray(g['coordinates'])
            if 'multi' in g['type'].lower():
                # flatten first two dim
                xy = xy.reshape(((xy.shape[0]*xy.shape[1],)+ xy.shape[2:]))
            for row in range(xy.shape[0]):
                i={'points' : xy[row,:,:],'name': info['name']+'_'+item.id}
                if 'polygon' in g['type'].lower():
                    self.user_polygons.append(i)


        ml.progress_marker(f'Read user coordinates named "{info["name"]}" from file "{params["file_name"]}" ')
        ml.progress_marker(f'found {len(self.user_polygons):d} polygons',tabs=2)

    def _decompose_polygons(self, d):
        si = self.shared_info
        info= self.info

        for p in d:
            g = p['geometry']
            c= np.asarray(g['coordinates'])
            match g['type'].lower():
                case 'polygon':
                    coords.append(dict(name=g['id'], points=g['geometry']['coordinates']))
                case 'multipolygon':
                    pass





