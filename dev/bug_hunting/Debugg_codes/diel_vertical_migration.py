import numpy as np
from oceantracker.velocity_modifiers._base_velocity_modifer import _VelocityModiferBase

from oceantracker.util.parameter_checking import ParamValueChecker as PVC
from oceantracker.util.cord_transforms import NZTM_to_WGS84
import datetime 
import pytz
from pysolar import solar
from oceantracker.util.numba_util import njitOT

from oceantracker.shared_info import shared_info as si

class DielVerticalMigration(_VelocityModiferBase):
    """
    DielVerticalMigration moves particles to specific water depth to reproduce the daily vertical migrations performed by planktonic organisms
    """
    
    def __init__(self,):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaults
        self.add_default_params({'vertical_swimming_speed': PVC(None, float, is_required=True, min=0., max=1.0e10, units='millimiters.seconds^-1', doc_str='Vertical swimming speed during diel vertical migrations'),
                                 'vertical_position_daytime': PVC(None, float, is_required=True, min=-100., max=0., units='meters', doc_str='Central position of plankton during daytime'),
                                 'vertical_position_nighttime': PVC(None, float, is_required=True, min=-100., max=0., units='meters', doc_str='Central position of plankton during nighttime'),
                                 'age_start': PVC(0., float, is_required=True, min=0., units='seconds', doc_str='Age of particles to start diel vertical migrations'),
                                 })


    def check_requirements(self):
        self.check_class_required_fields_prop_etc(requires3D=True, required_props_list=['velocity_modifier'])        
  
  
    def initial_setup(self):
        super().initial_setup()
        pgm= si.core_class_roles.particle_group_manager
        si.add_class('particle_properties',name='light',class_name='ManuallyUpdatedParticleProperty',initial_value=0., description='Solar radiation currently experienced by particles in umol/m2/s-1')

    
    def calculateMaxSunLight(self,date,x,light,sel):
        # Calculates the max sun radiation at given positions and dates (and returns zero for night time)
        # 
        # The method is using the third party library PySolar : https://pysolar.readthedocs.io/en/latest/#
        # 
        # some other available options:
        # https://pypi.org/project/solarpy/
        # https://github.com/trondkr/pyibm/blob/master/light.py
        # use calclight from Kino Module here  : https://github.com/trondkr/KINO-ROMS/tree/master/Romagnoni-2019-OpenDrift/kino
        # ERcore : dawn and sunset times : https://github.com/metocean/ercore/blob/ercore_opensrc/ercore/lib/suncalc.py
        # https://nasa-develop.github.io/dnppy/modules/solar.html#examples
        # 
        dtObject_local = date.flatten()[0]
        dtObject_utc = dtObject_local.astimezone(pytz.timezone('UTC')) # set datetime to UTC
        si.msg_logger.msg('Assuming UTC time for solar calculations')
        
        # Select moving particles only
        # longitude convention in pysolar: negative reckoning west from prime meridian in Greenwich, England
        # The particle longitude should be converted to the convention [-180,180] if that is not the case
        lon_lat_z = NZTM_to_WGS84(x[sel])
        sun_altitude = solar.get_altitude(lon_lat_z[:, 0], lon_lat_z[:, 1], dtObject_utc) # get sun altitude in degrees
        sun_azimuth = solar.get_azimuth(lon_lat_z[:, 0], lon_lat_z[:, 1], dtObject_utc) # get sun azimuth in degrees
        sun_radiation = np.zeros(len(sun_azimuth))
        # not ideal get_radiation_direct doesnt accept arrays...
        for elem_i,alt in enumerate(sun_altitude):
            sun_radiation[elem_i] = solar.radiation.get_radiation_direct(dtObject_utc, alt)  # watts per square meter [W/m2] for that time of day
        # save compute light for each moving particle
        light[sel] = sun_radiation * 4.6 #Converted from W/m2 to umol/m2/s-1"" - 1 W/m2 ≈ 4.6 μmole.m2/s
        #
        si.msg_logger.msg('Solar radiation from %s to %s [W/m2]' % (sun_radiation.min(), sun_radiation.max() ) )
    
    def update(self, n_time_step, time_sec, active):
        
        part_prop = si.class_roles.particle_properties
        
        # Compute solar radiation for active particles
        date = si.run_info.current_model_date.astype(datetime.datetime) # make the datetime object aware of timezone
        self.calculateMaxSunLight(date,part_prop['x'].data,part_prop['light'].data,active)
        
        # Modify vertical velocity to follow diel vertical migration
        vertical_velocity = np.abs(self.params['vertical_swimming_speed']) /1000  # magnitude in mm/s 
        start = self.params['age_start'] # Start of diel vertical migration (age in seconds)
        self._update_diel_vertical_velocity(part_prop['velocity_modifier'].data, 
                                            part_prop['light'].data, 
                                            part_prop['age'].data,
                                            start,                                            
                                            part_prop['x'].data,
                                            vertical_velocity,
                                            self.params['vertical_position_daytime'],
                                            self.params['vertical_position_nighttime'],
                                            active) 
  
    @staticmethod    
    @njitOT
    def _update_diel_vertical_velocity(w, light, age, start, x, vertical_velocity, z_day, z_night, active): 
        ''' Diel vertical migration for planktonic organisms '''
        # Particles are assumed to move to daytime or nighttime vertical positions in the water column, at a constant rate
        # it is expected that particles will go down during day time and up during night time but that is not fixed in the code. 
        # Particles will simply go towards the daytime or nighttime positions.
        #for particles in daytime : particles below the daytime position need to go up while particles above the daytime position need to go down
        #(same for particles in nighttime)
        #Note : depth convention is negative down in OceanTracker
        #e.g. z=-5, z_day = -3, below daytime position,  need to go up (vertical_velocity>0) 
        #     diff = (z - z_day) = -2, so w = - np.sign(diff) * vertical_velocity
        for n in active:
            if age[n] > start:             
                if light[n] > 0:
                    d =  - np.sign(x[n,2] - z_day) 
                else:
                    d = - np.sign(x[n,2] - z_night) 
                w[n,2] += d  * vertical_velocity
                pass
        return
        
        ## Python array type code 
        # competent_larvae = part_prop['age'].data > self.params['start']
        # si.msg_logger.msg('Plankton : update_terminal_velocity - %s particles moving up and down' % (competent_larvae.sum()) )
        # if competent_larvae.any() > 0 :
            # self.calculateMaxSunLight() # compute solar radiation at particle positions (using PySolar)
            # z_day = self.params['vertical_position_daytime']     #  the depth a species is expected to inhabit during the day time, in meters, negative down') #
            # z_night = self.params['vertical_position_nighttime'] # 'the depth a species is expected to inhabit during the night time, in meters, negative down') #
            
            # ind_day = np.where(competent_larvae & (part_prop['light'].data>0))
            # ind_night = np.where(competent_larvae & (part_prop['light'].data == 0))
            # si.msg_logger.msg('Using constant migration rate (%s m/s) towards day and night time positions' % (vertical_velocity) )
            # si.msg_logger.msg('%s particles in day time' % (len(ind_day[0])))
            # si.msg_logger.msg('%s particles in night time' % (len(ind_night[0])))

            
            # part_prop['velocity_modifier'].data[ind_day, 2] += - np.sign(part_prop['x'].data[ind_day, 2] - z_day) * vertical_velocity
            # part_prop['velocity_modifier'].data[ind_night, 2] += - np.sign(part_prop['x'].data[ind_night, 2] - z_night) * vertical_velocity
