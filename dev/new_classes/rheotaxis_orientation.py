import numpy as np
from oceantracker.velocity_modifiers._base_velocity_modifer import _VelocityModiferBase
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
from numba import njit
from oceantracker.util.numba_util import njitOT

from oceantracker.shared_info import shared_info as si

class RheotaxisOrientation(_VelocityModiferBase):
    """
    RheotaxisOrientation moves particles against the local current to reproduce the rheotaxis swimming behaviour observed in Inanga.
    Author : Romain Chaput 
    Under development - first draft: 12/12/2024 - Last update: 
    """
    
    def __init__(self,):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaults
        self.add_default_params({'horizontal_swimming_speed_hatch': PVC(None, float, is_required=True, min=0., max=1.0e10, units='centimeters.seconds^-1',
                                                                        doc_str='Horizontal swimming speed at hatching'),
                                 'horizontal_swimming_speed_settle': PVC(None, float, is_required=True, min=0., max=1.0e10, units='centimeters.seconds^-1',
                                                                         doc_str='Horizontal swimming speed at settlement'),
                                 'PLD': PVC(None, float, is_required=True, min=0., max=1.0e10, units='seconds', doc_str='Maximum age of larvae'),
                                 'start_orientation': PVC(None, float, is_required=True, min=0., units='seconds', doc_str='Age of particles to start orientation'),
                                 'Lambda': PVC(None, float, is_required=True, min=0., max=1.0e10, units='none', doc_str='Orientation accuracy. Variance of Von Mises distribution.'),
                                 'station_holding': PVC(False, bool, doc_str='Position holding behaviour,false by default to allow fish to swim upstream'),
                                 })


    def check_requirements(self):
        self.check_class_required_fields_prop_etc(requires3D=True, required_props_list=['velocity_modifier'])        
  
  
    def initial_setup(self):
        super().initial_setup()                          

        
#    def reset_horizontal_swimming(self, active):
#		# Create a  vector for swimming movement: to update a each timestep to avoid accumulating swimming speed
#        part_prop = si.roles.particle_properties
#        part_prop['velocity_modifier'].data[:, 0] = np.array([0.0]*len(part_prop['x'].data), active)
#        part_prop['velocity_modifier'].data[:, 1] = np.array([0.0]*len(part_prop['x'].data), active)
    
    def rheotaxis_orientation(self, active):
        """"Orientation against the direction of the local currents
        """			
        part_prop = si.class_roles.particle_properties

        # Compute water velocity at particle positions
        currents = part_prop['water_velocity']

        # Compute randomness of direction
        ti  = np.random.vonmises(0, self.params['Lambda'], len(active)) # To draw for all active particles

        # Compute swimming direction and speed for station holding or upstream swimming
        if self.params['station_holding']==True:
            self._update_station_holding(currents.data, 
                                        ti, 
                                        part_prop['age'].data,
                                        self.params['start_orientation'],                                            
                                        self.params['horizontal_swimming_speed_hatch'],
                                        self.params['horizontal_swimming_speed_settle'],
                                        self.params['PLD'],
                                        active,
                                        part_prop['velocity_modifier'].data,
                                        )
        else:
            self._update_upstream_swimming(currents.data, 
                                        ti, 
                                        part_prop['age'].data,
                                        self.params['start_orientation'],                                            
                                        self.params['horizontal_swimming_speed_hatch'],
                                        self.params['horizontal_swimming_speed_settle'],
                                        self.params['PLD'],
                                        active,
                                        part_prop['velocity_modifier'].data,
                                        )


    @staticmethod    
    @njitOT
    def _update_station_holding(uv, ti, age, start, hatch, settle, PLD, active, velocity_modifier): 
        ''' Rheotaxis orientation for larvae with station holding '''
        # 
        for n in active:
            if age[n] > start:
                # Compute angle in relation to current
                thetaRheo = (np.arctan2(uv[n, 1], uv[n, 0])+ np.pi)%(2*np.pi)
                theta = thetaRheo + ti[n]
                # Compute current speed absolute value
                UV = np.sqrt(uv[n,0]**2 + uv[n,1]**2)
                # Compute norm of swimming speed
                hor_swimming_speed = (hatch + (settle - hatch)** (np.log(age[n])/np.log(PLD)))/ 100
                norm_swim = np.abs(hor_swimming_speed)

                if norm_swim < UV:
                    # Compute u and v velocity and make larvae swim against the flow
                    velocity_modifier[n, 0] += hor_swimming_speed*np.cos(theta)
                    velocity_modifier[n, 1] += hor_swimming_speed*np.sin(theta)
                else:
                    # Larvae match currents velocity and remain in one spot
                    velocity_modifier[n, 0] += UV*np.cos(theta)
                    velocity_modifier[n, 1] += UV*np.sin(theta)


    @staticmethod    
    @njitOT
    def _update_upstream_swimming(uv, ti, age, start, hatch, settle, PLD, active, velocity_modifier): 
        ''' Rheotaxis orientation for larvae '''
        # 
        for n in active:
            if age[n] > start:
                # Compute angle in relation to current
                thetaRheo = (np.arctan2(uv[n, 1], uv[n, 0])+ np.pi)%(2*np.pi)
                theta = thetaRheo + ti[n]
                # Compute norm of swimming speed
                hor_swimming_speed = (hatch + (settle - hatch)** (np.log(age[n])/np.log(PLD)))/ 100

                # Possibility for fish to swim faster than currents
                velocity_modifier[n, 0] += hor_swimming_speed*np.cos(theta)
                velocity_modifier[n, 1] += hor_swimming_speed*np.sin(theta)



    def update(self, n_time_step, time_sec, active):        
#        self.reset_horizontal_swimming()
        self.rheotaxis_orientation(active)

