# basic definitions
# to avoid circular imports definitions.py file cannot import any oceantracker modules

package_fancy_name= 'OceanTracker'

from os import path, sep
import subprocess, sys
from dataclasses import  dataclass, asdict
from importlib.metadata import version as get_version

version= dict()
v = version
v['oceantracker_version'] = get_version("oceantracker")
v['major'],v['minor'],v['micro'],v['patch'] = [int(v) for v in v['oceantracker_version'].split('.')]

try:
    version['git_commit_hash'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=path.dirname(path.realpath(__file__))).decode().replace('\n', '')
except:
    version['git_commit_hash'] = 'unknown'
try:
    version['date'] = subprocess.check_output(['git', 'log', '-1', '--format=%cd'], cwd=path.dirname(path.realpath(__file__))).decode().replace('\n', '')
except:
    version['date'] = 'unknown'

version.update(
    python_version = sys.version,
    python_major_version= sys.version_info.major,
    python_minor_version = sys.version_info.minor, 
    python_micro_version= sys.version_info.micro,
    )



docs_base_url= 'https://oceantracker.github.io/oceantracker/_build/html/'
package_dir = path.dirname(__file__)
ot_root_dir = path.dirname(package_dir)
default_output_dir = path.join(path.dirname(ot_root_dir),'oceantracker_output')

#todo automate build of known readers list
known_readers = dict(
                SCHISM= 'oceantracker.reader.SCHISM_reader.SCHISMreader',
                ROMS =  'oceantracker.reader.ROMS_reader.ROMSreader',
                SCHISM_v5 =  'oceantracker.reader.SCHISM_reader_variants.SCHISMreaderV5',

                GLORYS =  'oceantracker.reader.GLORYS_reader.GLORYSreader',
                DELFT3D_FM =  'oceantracker.reader.DELFT3DFM_reader.DELFT3DFMreader',
                FVCOMreader =  'oceantracker.reader.FVCOM_reader.FVCOMreader',
                # known variants of readers
                ROMSmoanaProject = 'oceantracker.reader.ROMS_reader_variants.ROMSreaderMoanaProjectNZ',
                SCHISM_CSIRO_CCHAPS =  'oceantracker.reader.SCHISM_reader_variants.SCHISMreader_CSIRO_CCAHPS',
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

class _AttribDict():
    '''
    holds variables as class attributes to enable auto-complete hints
    and give iterators over these variables, but can act like a dictionary,
    ie  allows both  instance.backtracking and instance['backtracking']
    '''
    def __init__(self):
        # add  class variables in ._class_.__dict__, to instance __dict__ by adding attributes
        for key, item in self.__class__.__dict__.items():
            if not key.startswith('_'):
                setattr(self, key, item)
        pass

    def asdict(self): return self.__dict__

    def keys(self): return  self.__class__.__dict__

    def possible_values(self):  return list(self.__dict__.keys())

    def items(self): return  self.__dict__.items()

    def __getitem__(self, name:str):  return getattr(self,name)
    def __setitem__(self, name:str, value):  setattr(self,name, value)


''' Particle status flags mapped to integer values '''
class _ParticleStatusFlags(_AttribDict):
    unknown : int = -20
    notReleased : int = -10
    dead : int = -5
    outside_domain: int = -2
    outside_open_boundary : int = -1
    stationary : int = 0
    stranded_by_tide : int = 3
    on_bottom : int = 6
    moving : int = 10

# status of cell search

class _CellSearchStatusFlags(_AttribDict):
    ok: int = 0
    hit_domain_boundary: int = -1
    hit_open_boundary: int = -2
    hit_dry_cell : int = -3
    bad_coord: int = -20
    failed: int = -30

# types of node
class _NodeTypes(_AttribDict):
    interior: int = 0
    island_boundary: int = 1
    domain_boundary: int = 2
    open_boundary: int = 3
    land: int = 4

class _EdgeTypes(_AttribDict):
    interior: int = 0
    domain: int = -1
    open_boundary: int = -2

class _DimensionNames(_AttribDict):
    # used to standardise netcdf output dimension names
    # sizes set on file setupwith create_dimension
    time: str = 'time_dim'
    particle: str  = 'particle_dim'
    vector2D: str  = 'vector2D'
    vector3D: str = 'vector3D'
    triangle: str = 'triangle_dim'
    age: str = 'age_dim'
    grid_row_y: str = 'row_y_dim'
    grid_col_x: str = 'col_x_dim'
    z: str = 'z_dim'
    node  = 'node_dim'
    cell = 'cell_dim'
    release_group= 'release_group_dim'
    polygons= 'polygon_dim'
    age_bin_edges= 'age_bin_edges_dim'
    age_bin = 'age_bin_dim'



cell_search_status_flags = _CellSearchStatusFlags()

