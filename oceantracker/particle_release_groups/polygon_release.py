import numpy as np
from oceantracker.util.polygon_util import InsidePolygon
from oceantracker.particle_release_groups.point_release import PointRelease
from oceantracker.util.parameter_checking import ParamDictValueChecker as PVC, GracefulExitError
from oceantracker.common_info_default_param_dict_templates import default_polygon_dict_params


class PolygonRelease(PointRelease):
    # random polygon release in 2D or 3D

    def __init__(self):
        # set up info/attributes
        super().__init__()
        self.add_default_params(default_polygon_dict_params)
        self.add_default_params({'z_min': PVC(0.,float, doc_str='Min. z cord value to release with the polygon'),
                                 'z_max': PVC(0., float, doc_str='Max. z cord value to release with the polygon'),
                                 'allow_release_in_dry_cells' :  PVC(False, bool,
                                        doc_str='Allow releases in cells which are currently dry, ie. either permanently dry or temporarily dry due to the tide'),
                                })
        self.class_doc(description='Release particles at random locations within given polygon. Points chosen are always inside the domain, also inside wet cells unless  allow_release_in_dry_cells is True.')

        # below are not needed for polygons
        self.remove_default_params(['release_radius'])


    def initialize(self):
        # sort out list  polygon from points
        info = self.info
        si= self.shared_info
        points = np.array(self.params['points']).astype(np.float64)

        if points.shape[0] < 3:
            si.case_log.write_msg('For polygon release group  "points" parameter have at least 3 points, given ' + str(points), exception = GracefulExitError)

        self.polygon = InsidePolygon(verticies = points[:,:2])

        info['points'] =  self.polygon.points

        area = self.polygon.get_area()

        if area < 1:
            si.case_log.write_msg('Release group = ' + str(self.instanceID)
                           + ', a Polygon release, area of polygon is practically zero , cant release particles from polygon as shape badly formed, area =' + str(area), exception = GracefulExitError)

        info['number_released'] = 0
        info['pulse_count'] = 0


    def estimated_total_number_released(self):
        npart = self.params['pulse_size'] * self.release_schedule_times.shape[0]
        npart = int(npart + max(10, .03 * npart))  # add 1% more
        return npart

    def release_locations(self):
        # set up full set of release locations inside  polygons
        si = self.shared_info
        info= self.info
        self.code_timer.start('Polygon release-release_locations')
        bounds = self.polygon.polygon_bounds
        n_required = self.params['pulse_size']

        x0           = np.full((0, 2), 0.)
        n_cell_guess = np.full((0,), 0)
        count = 0
        n_found = 0

        while x0.shape[0] < n_required:
            xi = np.random.uniform(low=bounds[0], high=bounds[1], size=n_required)
            yi = np.random.uniform(low=bounds[2], high=bounds[3], size=n_required)
            xy_candidates = np.stack((xi, yi), axis=1)

            # select those inside polygon and domain
            sel = self.polygon.inside_indices(xy_candidates)
            x = xy_candidates[sel, :]

            # use KD tree to find points those outside model domain
            sel, n_cell = si.classes['interpolator'].are_points_inside_domain(x)

            # keep those inside domain
            x=x[sel,:]
            n_cell= n_cell[sel]

            # add keep only those in wet cells, crudely this is those not in dry cell at this and the next time step
            if not self.params[ 'allow_release_in_dry_cells']:
                nb = si.classes['field_group_manager'].get_current_reader_time_buffer_index()
                sel = np.logical_and(si.grid['is_dry_cell'][nb, n_cell] ==0, si.grid['is_dry_cell'][nb+1, n_cell] ==0)
                x=x[sel,:]
                n_cell= n_cell[sel]

            if x.shape[0] > 0:
                x, n_cell = self.filter_release_points(x, n_cell)

            # if any ok then add to list
            if x.shape[0]> 0:
                n_found += x.shape[0]
                x0          = np.concatenate((x0, x), axis =0)
                n_cell_guess= np.concatenate((n_cell_guess, n_cell))

            # allow 20 cycles to find points
            count += 1
            if count > 20*n_required: break

        if n_found < n_required  :
            si.case_log.write_warning('Polygon release, only found ' + str(n_found) + ' of ' + str(n_required) + ' required points inside polygon after 20 cycles')
            n_required = n_found #

        # trim initial location and cell  to required number
        x0 = x0[:n_required, :]
        n_cell_guess = n_cell_guess [:n_required]

        if si.hindcast_is3D:
            x0= np.hstack((x0,np.random.uniform(self.params['z_min'],self.params['z_max'], x0.shape[0]).reshape((-1,1))))

        n = x0.shape[0]
        IDrelease_group = np.repeat(self.instanceID,n )
        IDpulse = np.repeat(info['pulse_count'], n)
        info['pulse_count'] += 1
        user_release_group_ID = np.repeat(self.params['user_release_group_ID'],n)

        info['number_released'] += IDrelease_group.shape[0]  # count number released in this group

        self.code_timer.stop('Polygon release-release_locations')

        return x0, IDrelease_group, IDpulse, user_release_group_ID, n_cell_guess

    def filter_release_points(self, xy, n_cell):
        # user can filter release points by inhertitance of this class and overriding this method
        return xy, n_cell