# does gridded and polygon statistics for particles in a depth range

import oceantracker.particle_statistics.gridded_statistics as gridded_statistics
import oceantracker.particle_statistics.polygon_statistics as polygon_statistics
from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import ParamDictValueChecker as PVC
from numba import njit
from oceantracker.common_info_default_param_dict_templates import particle_info

class TopBottomLayerStats(ParameterBaseClass):
    # methods to add depth range selection merge into basic stats via inheritance
    def __init__(self):
        # set up info/attributes
        super().__init__()
        self.add_default_params({'min_status': PVC('frozen',str,possible_values=particle_info['status_flags'].keys()),
                                 'max_status': PVC('moving',str,possible_values=particle_info['status_flags'].keys()),
                                 'layer_thick_ness': PVC(0.000, float, min=0.),
                                 'top_layer': PVC(True, bool)}) # false for bottom layer

    def check_requirements(self):
        msg_list = self.check_class_required_fields_properties_grid_vars_and_3D(requires3D=True)
        if self.params['min_status'] > self.params['max_status']:
            msg_list.append('Error>> statistics param, range to count status,   min_status must be <= max_status' )
        return msg_list

#todo add min status to sel and as param
    def select_particles_to_count(self, out):
        # count particles in less than given water depth with status large enough
        si = self.shared_info
        grid = si.classes['reader'].grid

        status = si.classes['particle_properties']['status'].dataInBufferPtr()
        z  = si.classes['particle_properties']['x'].dataInBufferPtr()[:,2]
        bottom_cell_index = grid['bottom_cell_index']

        sel= self.select_inlayer(z, status, self.params['min_status'],self.params['max_status'],tide, water_depth,
                                           self.params['layer_thick_ness'], self.params['top_layer'], out)
        return sel

    @staticmethod
    @njit
    def select_inlayer(z, status, min_status, max_status, tide, water_depth, layer_thick_ness, count_in_top_layer, out):
        nfound = 0
        for n in range(status.shape[0]):
           if min_status <= status[n] <= max_status:
                if (count_in_top_layer and z[n] > tide[n]-layer_thick_ness) or z[n] < water_depth[n]+layer_thick_ness:
                    out[nfound] = n
                    nfound += 1
        return out[:nfound]

class GriddedStats2D_timeBasedTopBottom(TopBottomLayerStats, gridded_statistics.GriddedStats2D_timeBased):
    def __init__(self):
        # set up info/attributes
        super().__init__()
        # set up info/attributes
        self.add_default_params({'role_output_file_tag' : PVC('stats_gridded_time_layer', str)})

class GriddedStats2D_ageBasedTopBottom(TopBottomLayerStats, gridded_statistics.GriddedStats2D_agedBased):
    def __init__(self):
        # set up info/attributes
        super().__init__()
        # set up info/attributes
        self.add_default_params({'role_output_file_tag' : PVC('stats_gridded_age_layer', str)})

class PolygonStats2D_timeBasedTopBottom(TopBottomLayerStats, polygon_statistics.PolygonStats2D_timeBased):
    def __init__(self):
        # set up info/attributes
        super().__init__()
        # set up info/attributes
        self.add_default_params({'role_output_file_tag' : PVC('stats_polygon_time_depth_layer',str)})

class PolygonStats2D_ageBasedTopBottom(TopBottomLayerStats, polygon_statistics.PolygonStats2D_ageBased):
    def __init__(self):
        # set up info/attributes
        super().__init__()
        # set up info/attributes
        self.add_default_params({'role_output_file_tag' : PVC('stats_polygon_age_depth_layer', str)})