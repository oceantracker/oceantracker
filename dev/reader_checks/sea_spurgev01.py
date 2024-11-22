import  argparse
from os import path,chdir, mkdir


import  sys
from oceantracker.util import json_util, yaml_util
from oceantracker.main import OceanTracker

if __name__ == "__main__":
    # nested schisim, glorys

    input_dir1 = r'D:\Hindcast_reader_tests\Glorys\glorys_seasuprge'
    file_mask1='cmems_mod_glo_phy*.nc'
    #input_dir1=r'D:\Hindcast_reader_tests\Glorys\ocean_num_glorys'
    #file_mask1='glorys_reanalysis_surface*.nc'

    input_dir2 = r'Z:\Hindcasts\NZ_region\2024_OceanNumNZ-2022-06-20\final_version\2012\09'
    output_dir = r'D:\OceanTrackerOutput'

    ot = OceanTracker()
    ot.settings(output_file_base = 'sea_spurge01',root_output_dir=output_dir)
    ot.add_class('reader',input_dir=input_dir1,
                 file_mask = file_mask1)
    #ot.add_class('nested_readers',input_dir=input_dir2, file_mask = 'NZfinite*.nc',)


    pulse_size = 5


    file_mask = 'NZfinite*.nc'
    max_days = 5  # 30
    open_boundary_type = 1



    #x0 = cord_transforms.WGS84_to_NZTM(np.flip(np.asarray(x0), axis=1)).tolist()
    x0 = [[1727195, 6035149],
          [1737357, 6029638],
          [1742484, 6021345],
          [1743472, 6019861]]
    x0 = [ [174.665532083399,-35.922300421719214], ]  # hen and chickes, in outer grid
    ot.add_class('release_groups',points = x0)

    ot.run()



