from os import path, scandir
import argparse
from oceantracker.main import OceanTracker
from oceantracker.util import json_util
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="A simple script to greet a user.")
    parser.add_argument('-full',   action="store_true",  help="long demo hindcasts")
    parser.add_argument('-test', type=int,default=-1)
    args = parser.parse_args()

    folder =  r'F:\H_Local_drive\ParticleTracking\demo_hindcasts' if args.full else None

    subfolders = [ f.path for f in scandir(folder) if f.is_dir() ]

    for n, input_dir in  enumerate(subfolders):
        if args.test>0 and args.test != n: continue
        file_base = path.basename(input_dir).split('.')[0]

        ot = OceanTracker()
        ot.settings(root_output_dir=r'D:\OceanTrackerOutput\test_hindcast_readers', output_file_base=file_base)
        ot.add_class('reader',  input_dir= input_dir, file_mask=file_base+'*.nc' )

        info = json_util.read_JSON(path.join(input_dir,'info.json'))

        ot.add_class('release_groups',points=info['deep_point'])

        ot.run()
        pass
