from oceantracker.util.parameter_checking import ParamDictValueChecker as PVC, ParameterListChecker as PLC
from oceantracker.util.parameter_base_class import  ParameterBaseClass
from oceantracker.util.basic_util import nopass

# class to write with, outline methods needed
# a non-writer, as all methods are None

class BaseWriter(ParameterBaseClass):
    # particle property  write modes,   used to set when to write  properties to output, as well as if to calculate at all



    def __init__(self):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaults

        self.add_default_params({
                                'case_output_file_tag': PVC('tracks', str),
                                 'output_step_count': PVC(1,int,min=1),
                                 'turn_on_write_particle_properties_list': PLC(None, str),
                                 'turn_off_write_particle_properties_list': PLC(['water_velocity', 'particle_velocity'], str)  # todo add ablity to tweak write flags individually
                                 })
        self.info['output_file'] = None
        self.time_steps_written = 0

    def open_file(self): self.time_steps_written = 0
    def initialize(self,**kwargs): pass

    def pre_time_step_write_book_keeping(self): pass

    def post_time_step_write_book_keeping(self):  self.time_steps_written +=1

    def create_variable_to_write(self,name,first_dim_name,dim_len,**kwargs): pass

    def close(self): nopass()


