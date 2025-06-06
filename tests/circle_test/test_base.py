# Ocean particle tracker in pure python
# Ross Vennell Nov 2018


# profilers
# python -m cProfile
# python -m vmprof  <program.py> <program parameters>
# python -m cProfile -s cumtime
# -m bohrium
import numpy as np

from  oceantracker.main import  run
import argparse
import matplotlib.pyplot as plt
from os import path
import glob
from copy import copy
import time
from oceantracker.read_output.python import load_output_files
from oceantracker.plot_output import plot_tracks, plot_utilities


def plot_sample(caseInfoFile, num_to_plot=10 ** 3):
    # plot devation from circle

    data = load_output_files.load_track_data(caseInfoFile, ['x', 'age', 'water_depth', 'time', 'x0', 'ID'])
    grid= data['grid']


    nx = data['x'].shape[1]

    x = data['x']
    t   = (data['time']-data['time'][0])/ 24 / 3600
    x0 = data['x'][0,:,:]

    depth = data['water_depth']

    plt.figure()

    # grid and tracks
    plt.subplot(2, 2, 1)
    plt.plot(x[:, :, 0], x[:, :, 1], linewidth=.5)

    tl=''
    if x.shape[2] ==2:
        tl+='2D'
    else:
        tl += '3D'

    plt.title(tl)

    r0=np.sqrt(x0[:,0]**2+x0[:,1]**2)
    for r in r0:  # use r0 from main code
        plt.gcf().gca().add_artist(plt.Circle((0, 0), radius=r, color='black', fill=False, linestyle='--', linewidth=1))

    plot_utilities.draw_base_map(grid)
    plt.axis([-16000, 16000, -16000, 16000])

    ax=plt.subplot(2, 2, 2)
    mag = np.sqrt(x[:, :, 0]**2 + x [:, :, 1]**2)
    mag0 = np.sqrt(x0[:, 0]**2 + x0[ :, 1]**2)
    plt.plot(t, mag - mag0)
    plt.ylim([-1, 1])

    plt.text(0.1, .1, 'deviation from circle, m', transform=ax.transAxes)

# particle speed from change in positions is harsher test
    ax=plt.subplot(2, 2, 3)

    dt = (data['time'][-1]-data['time'][0])/data['time'].shape[0]
    v=np.diff(x,axis=0)/dt
    vmag = np.sqrt(v[:, :, 0] ** 2 + v[:, :, 1] ** 2)
    plt.plot(t[1:], vmag, linewidth=.5)
    plt.xlabel('days')
    plt.ylabel('speed')
    plt.text(0.1, .9, 'Particle Speed', transform=ax.transAxes)
    plt.ylim([0,2])
    ax=plt.subplot(2, 2, 4)

    if v.shape[2] ==2:
        plt.plot(t, depth, linewidth=.5)
        plt.xlabel('days')
        plt.text(0.1, .1, 'water depth', transform = ax.transAxes)
    else:
        plt.plot(t, x[:, :, 2], linewidth=.5)
        plt.xlabel('days')
        plt.ylabel('z')
        plt.text(0.1, .1, 'Particle z', transform=ax.transAxes)

    plt.show()

def plot_gridded_stats(log,seq_num, annotate_polygon=True, nfig=1):
    p = log['full_params']['particle_statistics'][seq_num]
    l=  log['info']['particle_statistics'][seq_num]

    if 'time' in p['name']:
        lab ="Time"
    else:
        lab ='Age'

    s = readOutputFiles.read_stats_file(l['file_name'], ['x', 'y', 'count', 'sum_water_depth', 'sum_age', 'sum_age_decay'])

    plt.figure()

    n_groups=s['x'].shape[0]

    # infer polygon file
    if annotate_polygon:
        pfile_mask= l['file_name'].replace('gridded','polygon').split('_0')
        pfile_name=glob.glob(pfile_mask[0]+'*.nc')[0]
        poly = readOutputFiles.read_polygon_stats(pfile_name, var_list=['count', 'sum_water_depth', 'sum_age', 'sum_age_decay'])


    for ng in range(n_groups):
        xi,yi = np.meshgrid(s['x'][ng,:],s['y'][ng,:])
        np1= ng*4  # 4 subplot

        count = np.nansum(s['count'][:, ng, :, :].astype(np.float64),axis=0)
        count[count==0.] = np.nan

        plt.subplot(n_groups, 4, 1 + np1)
        z=copy(count)
        z[z == 0.] = np.nan
        z2=np.full_like(xi,np.nan)
        sel=z >0
        z2[sel]= np.log10(z[sel])
        plt.pcolor(xi, yi, z)
        plt.colorbar()
        plt.title(lab +', Count Log_10',fontsize=6)
        plt.xticks([])
        plt.yticks([])
        if annotate_polygon:
            polygon_count= np.sum(poly['count'][:,ng,:].astype(np.float64),axis=0)
            polygon_anotation(poly,polygon_count)


        plt.subplot(n_groups, 4, 2 + np1)
        z = np.nansum(s['sum_water_depth'][:, ng, :, :], axis=0)/count
        plt.pcolor(xi, yi, z)
        plt.colorbar()
        plt.title('Depth',fontsize=6)
        plt.xticks([])
        plt.yticks([])
        if annotate_polygon:
            polygon_anotation(poly, np.nansum(poly['sum_water_depth'][:, ng, :], axis=0)/polygon_count)

        plt.subplot(n_groups, 4, 3 + np1)
        z = np.nansum(s['sum_age'][:, ng, :, :],axis=0)/count/24/3600
        plt.pcolor(xi, yi, z)
        plt.colorbar()
        plt.title('Age, days',fontsize=6)
        plt.xticks([])
        plt.yticks([])
        if annotate_polygon:
            polygon_anotation(poly, np.nansum(poly['sum_age'][:, ng, :] , axis=0)/polygon_count/24/3600)

        plt.subplot(n_groups, 4, 4 + np1)
        z = np.nanmean(s['sum_age_decay'][:, ng, :, :]/count,axis=0)
        plt.pcolor(xi, yi, z)
        plt.colorbar()
        #plt.text(0, 0, 'decay')
        plt.title('Unit age decay',fontsize=6)
        plt.xticks([])
        plt.yticks([])
        if annotate_polygon:
            polygon_anotation(poly, np.nansum(poly['sum_age_decay'][:, ng, :] , axis=0)/ polygon_count)

def polygon_anotation( poly,data):

    for n,p in enumerate(poly['info']['info']['polygon_list']):
        xy = np.array(p['points'])
        plt.plot(xy[:,0],xy[:,1])
        plt.text(xy[0, 0], xy[0, 1], str(np.round(data[n],2) ),fontsize=8)


def time_check_plot(runCaseInfo):
    data = load_output_files.load_track_data(runCaseInfo, ['time', 'age', 'ID'])
    nx = data['age'].shape[1]

    sel = np.sort(np.random.default_rng().choice(nx, size=30, replace=False))

    plt.figure()
    plt.subplot(3, 1, 1)

    t = (data['time'] - data['time'][0]) / 24 / 3600

    plt.plot(t,data['time'] )
    plt.title('time, days')

    plt.subplot(3, 1, 2)
    dt =np.diff(data['time'],axis=0)
    plt.plot(t[:-1],dt)
    plt.axis([0,t[-1],  np.nanmean(dt) - 50, np.nanmean(dt) + 50])
    plt.title('time diff, seconds')

    plt.subplot(3, 1, 3)
    plt.plot(t,data['age'][:, sel] / 24 / 3600)

    plt.title('Age')
    plt.show()

def base_param(is3D=False, isBackwards = False):

    # for speed comparisons with Scipy make sure AH>0 otherwise its last particle recycling trick helps it

    r0 = np.array([2000., 4000., 8000, 10000])  # no bad starts

    # all of  pulse start at same location
    p0 = [[0, 2000.], [0, 4000.], [0, 8000.], [0, 10000.]]
    #poly0 = [[9000., 9000], [10000, 9000], [10000, 10000.]]

    outputdir = 'tests\\output'
    input_dir =path.normpath(path.join(path.split(__file__)[0],'testData'))

    params={ 'debug': True,
            'root_output_dir': outputdir,
            'output_file_base': 'test_particle',
            'backtracking': isBackwards,
           'write_tracks': True,
            'time_step': 15*60,
           'max_run_duration': 10. * 24 * 3600,
            'reader': {'class_name':	"oceantracker.reader.generic_unstructured_reader.GenericUnstructuredReader",
                  'file_mask' : 'circFlow2D*.nc', 'input_dir': input_dir,
                        'field_variable_map': {'water_velocity' : ['u','v'],'water_depth': 'depth','tide': 'tide' },
                        'dimension_map': {'node': 'node', 'time': 'time'},
                        'grid_variable_map': {'time': 'time', 'x': ['x','y'],
                                      'triangles': 'simplex',
                                       },
                         'time_buffer_size': 200,
                         'isodate_of_hindcast_time_zero': '2000-01-01'},


             'solver': {'RK_order': 4},  # 5min steps to mact OT v01 paper
             'particle_group_manager': {},
             'release_groups': {'mypoint':
                                    {'points': p0, 'pulse_size': 1, 'release_interval': 3600, 'user_release_groupID': 5,
                                    'max_age': 10 * 24 * 3600, 'user_release_group_name': 'A group',
                                    },

                                },
             'dispersion': {'A_H': 0.,'A_V':0.},

             'particle_properties': {'mydecay':{'class_name': 'oceantracker.particle_properties.age_decay.AgeDecay'},
                                     'mydistance':{'class_name': 'oceantracker.particle_properties.distance_travelled.DistanceTravelled'}
                                     },
    }

    if is3D:
        # tweak for circle flow 3D
        r=params['reader']
        r['field_variables'].update({ 'water_velocity' : ['u','v', 'w']})
        r['grid_variable_map'].update({'zlevel': 'zlevel'})
        r['dimension_map'].update({'z': 'zlevel'})
        r['file_mask'] = params['reader']['file_mask'].replace('2D', '3D')
        params['dispersion'].update({'A_H': 0.,'A_V': 0.})

    return params


def run_test(working_params):
    caseInfoFile = run(working_params)
    return caseInfoFile

if __name__ == '__main__':

    # windows/linux  data source

    parser = argparse.ArgumentParser()
    parser.add_argument('--test', nargs='?', const=0, type=int, default=1)
    parser.add_argument('--size', nargs='?', const=0, type=int, default=0)
    parser.add_argument('-scatch_tests', action='store_true')
    parser.add_argument('-dev', action='store_true')
    args = parser.parse_args()
    args.parallel= False

    print(args)
    if args.test is None:
        testList=range(3)
    else:
        testList=[args.test]

    t0 = time.time()

    for ntest in testList:
        # misc or development choices of classes

        if ntest==1:
            # zero dispersion test 2d/3D
            for is3D in [False]:
                for isBackwards in[False]:
                    params = base_param(is3D=is3D, isBackwards=isBackwards)
                    params['max_run_duration']= 14 * 24 * 3600.
                    params['dispersion'].update( {'A_H': 0.,'A_V':0.0})
                    if args.dev:
                        params['base_case_params'].update({'interpolator': {'class_name': 'oceantracker.interpolator.scatch_tests.vertical_walk_at_particle_location_interp_triangle_native_grid.InterpTriangularNativeGrid_Slayer_and_LSCgrid'}})
                        # params['base_case_params']['dispersion'].update({'A_V':0., 'A_H':0.})
                        # params['base_case_params']['release_groups'][0]['pulse_size']=1

                    caseInfoFile = run_test(params)
                    plot_sample(caseInfoFile)
                    time_check_plot(runInfoFile)

        elif ntest ==2:
            # large dispersion wall bc test
            for dry_cells in [False, True]:
                for is3D in [False]:
                    for isBackwards in [False, True]:
                        params = base_param(is3D=is3D, isBackwards=isBackwards)
                        params['reader']['max_run_duration'] = 1 * 24 * 3600.
                        params['base_case_params']['dispersion'].update({'A_H': 50.})
                        params['base_case_params']['release_groups'][0].update({'pulse_size': 10 ** 1})

                        runInfoFile = run_test(params)
                        trackdata= load_output_files.load_track_data(runInfoFile)
                        plot_tracks.plot_tracks(trackdata)



        elif ntest==3:
            # plotting scatch_tests, test dry cell
            dc = None if 1 == 0   else  'dry_cells'

            params={ 'duration': 6.*24*3600, 'dispersion': {'A_H': 10},
                                                          'particle_group_manager': {'pulse_size': 10 ** 1, 'release_interval': 1*3600},
                                                'reader' : {'grid_map' : {'dry_cells' : dc},'dry_water_depth': 4.}
                                                         }

            runInfoFile = run_test(args, params)
            plot_tracks.animate_particles(runInfoFile)


        elif ntest == 4:
            # plotting scatch_tests
            runInfoFile = run_test({'duration': 5. * 24 * 3600, 'dispersion': {'A_H': 0., 'A_V': 0.},
                                        'particle_group_manager': {'pulse_size': 10 ** 1, 'release_interval': 1 * 3600},
                                        'trajectory_modifiers':[{'class_name': 'oceantracker.resuspension.BasicResuspension'}],
                                    }, is3D=True)

            plot_sample(runInfoFile)





        elif ntest== 9999:
            # latest scatch_tests block
            args.plot = 0
            args.size = 0
            args.file = 1
            ot = run_test(args, params={'dispersion': {'A_H': 0.},
                                        'particle_group_manager': {'pulse_size': 5, 'release_interval': 300},
                                        # test newreader
                                        })

        print(' Total run time ' + '%5.2f' % (time.time() - t0))

