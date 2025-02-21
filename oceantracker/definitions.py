# basic definitions
# to avoid circular imports definitions.py file cannot import any oceantracker modules

package_fancy_name= 'OceanTracker'

from os import path
import subprocess, sys
from dataclasses import  dataclass, asdict

version= dict(major= 0.5, revision  = 30, date = '2025-01-28', parameter_ver=0.5)
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
default_output_dir = path.join(path.dirname(path.dirname(package_dir)),'oceantracker_output')

#todo automate build of known readers list
known_readers = dict(
                SCHISM= 'oceantracker.reader.SCHISM_reader.SCHISMreader',
                ROMS =  'oceantracker.reader.ROMS_reader.ROMSreader',
                SCHISM_v5 =  'oceantracker.reader.SCHISM_reader_v5.SCHISMreaderV5',
                GLORYS =  'oceantracker.reader.GLORYS_reader.GLORYSreader',
                DEFT3D_FM =  'oceantracker.reader.DEFT3DFM_reader.DELF3DFMreader',
                FVCOMreader =  'oceantracker.reader.FVCOM_reader.FVCOMreader',
                ROMSmoanaProject = 'oceantracker.reader.ROMS_reader_moana_project.ROMSreaderMonaProject'
                #generic =  'oceantracker.reader.generic_unstructured_reader.GenericUnstructuredReader',
                #dummy_data =  'oceantracker.reader.dummy_data_reader.DummyDataReader',

                 )

default_classes_dict = dict(
                solver= 'oceantracker.solver.solver.Solver',
                particle_properties='oceantracker.particle_properties._base_particle_properties.ParticleProperty',
                time_varying_info='oceantracker.time_varying_info._base_time_varying_info.TimeVaryingInfo',
                field_group_manager='oceantracker.field_group_manager.field_group_manager.FieldGroupManager',
                field_group_manager_nested='oceantracker.field_group_manager.dev_nested_grids_field_group_manager.DevNestedFields',
                particle_group_manager= 'oceantracker.particle_group_manager.particle_group_manager.ParticleGroupManager',
                tracks_writer = 'oceantracker.tracks_writer.track_writer_compact.CompactTracksWriter',
                interpolator = 'oceantracker.interpolator.interp_triangle_native_grid.InterpTriangularGrid',
                dispersion='oceantracker.dispersion.random_walk.RandomWalk',
                resuspension='oceantracker.resuspension.resuspension.Resuspension',
                tidal_stranding = 'oceantracker.tidal_stranding.tidal_stranding.TidalStranding',
                release_groups = 'oceantracker.release_groups.point_release.PointRelease',
                field_reader='oceantracker.fields.reader_field.ReaderField',
                field_custom='oceantracker.fields._base_field.CustomField',
                field_friction_velocity='oceantracker.fields.friction_velocity.FrictionVelocity',
                field_A_Z_profile_vertical_gradient='oceantracker.fields.field_vertical_gradient.VerticalGradient',
                )
# index values

# below are mapping names to index name, and are added to shared info
@dataclass
class _BaseConstantsClass:
    c = 1
    def asdict(self):  return self.__dict__
    def possible_values(self):  return list(self.__dict__.keys())


''' Particle status flags mapped to integer values '''
@dataclass
class _ParticleStatusFlags(_BaseConstantsClass):
    unknown : int = -20
    bad_coord : int = -16
    cell_search_failed: int = -15
    notReleased : int = -10
    dead : int = -5
    hit_dry_cell: int = -4
    outside_domain : int = -3
    outside_open_boundary : int = -2
    stationary : int = 0
    stranded_by_tide : int = 3
    on_bottom : int = 6
    moving : int = 10


# types of node
@dataclass
class _NodeTypes(_BaseConstantsClass):
    interior: int = 0
    island_boundary: int = 1
    domain_boundary: int = 2
    open_boundary: int = 3
    land: int = 4

@dataclass
class _EdgeTypes(_BaseConstantsClass):
    interior: int = 0
    domain: int = -1
    open_boundary: int = -2


# status of cell search
@dataclass
class _CellSearchStatusFlags(_BaseConstantsClass):
    ok: int = 0
    domain_edge: int = -1
    open_boundary_edge: int = -2
    dry_cell_edge : int = -3
    bad_coord: int = -20
    failed: int = -30

    def get_edge_vars(self):
        return {key:item for key,item in self.asdict().items() if key in ['domain_edge']}

cell_search_status_flags = _CellSearchStatusFlags()

