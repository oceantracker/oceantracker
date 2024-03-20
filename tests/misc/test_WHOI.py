from oceantracker.main import run, OceanTracker
from plot_oceantracker import plot_statistics, plot_tracks
from read_oceantracker.python import load_output_files
from os import path
import argparse


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument('-noplots', action='store_true')
    parser.add_argument('-norun', action='store_true')
    args = parser.parse_args()

    ncase = 1

    match ncase:
        case 1:

            root_input_dir= r'F:\Hindcasts\Hindcast_samples_tests\WHOI_calvin\schism_old_format'
            root_output_dir= 'F:\\OceanTrackerOtuput\\WHOI\\schism'
            output_file_base='WHOIschism'
            file_mask = 'sc*.nc'
            x0 =[[1780846.7742,       5938985.617],
                [1589852.1505,      6125208.1756]]

    ot = OceanTracker()

    ot.settings( output_file_base = output_file_base, root_output_dir =root_output_dir)

    ot.add_class('release_groups',name ='P1',points= x0 ,pulse_size=5, release_interval =  1800)
    ot.add_class('dispersion', A_H= 1.0 ,A_V= 0.001)

    ot.add_class('particle_statistics', name ='S1', class_name = 'oceantracker.particle_statistics.gridded_statistics.GriddedStats2D_timeBased',
                                 update_interval= 3600, particle_property_list = ['water_depth'],
                                 grid_center= x0[0],grid_span = [25000.,25000.],
                                 grid_size= [120, 121])
    ot.add_class('reader',  file_mask = file_mask, input_dir = root_input_dir)


    if not args.norun:
        caseInfoFile, has_errors= ot.run()

    else:
        run_dir= path.join(root_output_dir, output_file_base)
        caseInfoFile = load_output_files.get_case_info_files_from_dir(run_dir, case=1)

    # do plot
    if not args.noplots:

        ax=[800000,     2200000,     4400000,     6400000] # NZ
        ax=[1727860,     1823449,     5878821,     5957660] # Auck

        axBOP= [1856014.778854954,1978628.00674731, 5794851.51338963, 5889202.600050561]
        track_data = load_output_files.load_track_data(caseInfoFile)
        plot_tracks.animate_particles(track_data, axis_lims=ax, title='OceanNum NZ Schism test, fall velocity and critical friction  resuspension')
        plot_tracks.plot_path_in_vertical_section(track_data, title='OceanNum, fall velocity and critical friction  resuspension ')

        stats_data = load_output_files.load_stats_data((caseInfoFile))
        plot_statistics.animate_heat_map(stats_data, axis_lims=ax, title='OceanNum Schism, time based particle count heatmaps, built on the fly,  log scale', logscale=True)

        plot_statistics.plot_heat_map(stats_data, axis_lims=ax, var='water_depth', title='Water_depth, Time based Heat maps built on the fly, no tracks recorded')


