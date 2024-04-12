# basic defions
# to avoid circular imports definitions.py file cannot import any oceantracker modules



package_fancy_name= 'OceanTracker'

from os import path
import subprocess, sys

version= dict(major= 0.5, revision  = 1, date = '2024-03-30', parameter_ver=0.5)
version['str'] = f"{version['major']:.2f}.{version['revision']:04.0f}-{version['date']}"

try:
    version['git_revision'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=path.dirname(path.realpath(__file__))).decode().replace('\n', '')
except:
    version['git_revision'] = 'unknown'

version.update( python_version = sys.version,python_major_version= sys.version_info.major,
                python_minor_version = sys.version_info.minor, python_micro_version= sys.version_info.micro,)


max_timedelta_in_seconds = 1000*365*24*3600

docs_base_url= 'https://oceantracker.github.io/oceantracker/_build/html/'
package_dir = path.dirname(__file__)
ot_root_dir = path.dirname(package_dir)

known_readers = dict(
                schisim= 'oceantracker.reader.schism_reader.SCHISMreaderNCDF',
                schisim_v5 =  'oceantracker.reader.schism_reader_v5.SCHISMreaderNCDFv5',
                fvcom =  'oceantracker.reader.FVCOM_reader.unstructured_FVCOM',
                roms =  'oceantracker.reader.ROMS_reader.ROMsNativeReader',
                delft3d_fm =  'oceantracker.reader.dev_delft_fm.DELFTFM',
                generic =  'oceantracker.reader.generic_ncdf_reader.GenericUnstructuredReader',
                dummy_data =  'oceantracker.reader.dummy_data_reader.DummyDataReader',
                 )

node_types= dict(interior = 0,island_boundary = 1, domain_boundary= 2, open_boundary=3, land = 4)


default_classes_dict = dict(
                solver= 'oceantracker.solver.solver.Solver',
                particle_properties='oceantracker.particle_properties._base_particle_properties.ParticleProperty',
                time_varying_info='oceantracker.time_varying_info._base_time_varying_info.TimeVaryingInfo',
                field_group_manager='oceantracker.field_group_manager.field_group_manager.FieldGroupManager',
                particle_group_manager= 'oceantracker.particle_group_manager.particle_group_manager.ParticleGroupManager',
                tracks_writer = 'oceantracker.tracks_writer.track_writer_compact.CompactTracksWriter',
                interpolator = 'oceantracker.interpolator.interp_triangle_native_grid.InterpTriangularNativeGrid_Slayer_and_LSCgrid',
                dispersion_random_walk = 'oceantracker.dispersion.random_walk.RandomWalk',
                dispersion_random_walk_varyingAz ='oceantracker.dispersion.random_walk_varyingAz.RandomWalkVaryingAZ',
                resuspension_basic = 'oceantracker.resuspension.resuspension.BasicResuspension',
                tidal_stranding = 'oceantracker.tidal_stranding.tidal_stranding.TidalStranding',
                release_groups = 'oceantracker.release_groups.point_release.PointRelease',
                field_reader='oceantracker.fields._base_field.ReaderField',
                field_custom='oceantracker.fields._base_field.CustomField',
                field_friction_velocity_from_bottom_stress='oceantracker.fields.friction_velocity.FrictionVelocityFromBottomStress',
                field_friction_velocity_from_near_sea_bed_velocity='oceantracker.fields.friction_velocity.FrictionVelocityFromNearSeaBedVelocity',
                field_A_Z_profile_vertical_gradient='oceantracker.fields.field_vertical_gradient.VerticalGradient',
                )

