"""Reader for SHYFEM finite element model output, https://github.com/shyfemcm/shyfemcm

Developed against the ISMAR-CNR "EMERGE" Adriatic/Venice lagoon hindcasts,
https://iws.ismar.cnr.it/thredds/catalog/emerge/catalog.html

Notes on the file format
    * all fields are held at grid nodes, so no cell/edge to node interpolation is needed,
    * the vertical grid is fixed z levels, variable "level" holds the depth,
      positive down, of the *bottom* of each layer, so n_levels layers have
      n_levels+1 interfaces, with the topmost interface at the surface,
    * layers are ordered surface first, ie the opposite of OceanTracker's
      bottom-up z ordering, so data and levels are flipped on read,
    * cells below the sea bed are declared as _FillValue = -999, but not all output
      actually uses it, eg the EMERGE hindcasts pad them with zeros, so the bottom of
      each water column is taken from "total_depth" and the layer depths,
    * the element connectivity is often *not* in the files.  The EMERGE hindcasts
      were post processed with "ncks -C -x -v ... element_index", so the
      triangulation must be supplied by the model's ".grd" grid file via the
      "grd_file_name" parameter.
"""

from os import path

import numpy as np

from oceantracker.reader._base_unstructured_reader import _BaseUnstructuredReader
from oceantracker.reader.util import reader_util
from oceantracker.reader.util import hydromodel_grid_transforms as hg_trans
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterListChecker as PLC
from oceantracker.util.parameter_checking import ParameterMapAlternativesChecker as PMAC
from oceantracker.util.parameter_checking import ParameterListMapAlternativesChecker as PLMAC
from oceantracker.shared_info import shared_info as si


class SHYFEMreader(_BaseUnstructuredReader):
    development = True

    def __init__(self):
        super().__init__()  # required in children to get parent defaults and merge with give params
        self.add_default_params(
            grd_file_name=PVC(None, str,
                    doc_str='SHYFEM ".grd" grid file holding the element connectivity, required when the hindcast '
                            'files have no "element_index" variable, as is the case for the EMERGE Adriatic hindcasts'),
            one_based_indices=PVC(True, bool, doc_str='SHYFEM "element_index" node numbers start at 1, not zero'),
            regrid_z_to_sigma_levels=PVC(False, bool,
                    doc_str='Not used, SHYFEM output is on a fixed z grid which is not regridded to sigma levels'),
            load_fields=PLC(['water_depth'], str, doc_str='always load tide and water depth, needed for dry cells'),
            grid_variable_map=dict(
                    time=PMAC('time', doc_str='Name of time variable in hindcast'),
                    x=PMAC('longitude', doc_str='x location of nodes'),
                    y=PMAC('latitude', doc_str='y location of nodes'),
                    z_layer_bottom=PMAC('level', doc_str='depth, positive down, of the bottom of each layer'),
                    triangles=PMAC('element_index', doc_str='nodes of each element, only in some SHYFEM output'),
                    ),
            all_z_dims=PLC(['level'], str, doc_str='All z dims, used to identify  3D variables'),
            dimension_map=dict(
                    node=PMAC('node', doc_str='name of node dimension in files'),
                    z=PMAC('level', doc_str='name of the layer dimension in files'),
                    time=PMAC('time', doc_str='name of time dimension in files'),
                    ),
            field_variable_map={
                    'water_velocity': PLMAC(['u_velocity', 'v_velocity']),
                    'tide': PMAC('water_level', doc_str='maps standard internal field name to file variable name'),
                    'water_depth': PMAC('total_depth', doc_str='maps standard internal field name to file variable name'),
                    'water_temperature': PMAC('temperature', doc_str='maps standard internal field name to file variable name'),
                    'salinity': PMAC('salinity', doc_str='maps standard internal field name to file variable name'),
                    },
            )

    def initial_setup(self):
        # SHYFEM is a fixed z grid, there is nothing to regrid onto sigma levels
        self.params['regrid_z_to_sigma_levels'] = False
        super().initial_setup()

    def decode_time(self, time):
        # SHYFEM time units carry a trailing time zone name, eg "seconds since 2018-01-01 00:00:00 UTC",
        # which numpy's datetime64 will not parse, so drop it before the base class decodes the units
        units = time.attrs.get('units', '')
        if ' since ' in units:
            unit, date = units.split(' since ', 1)
            fields = date.strip().split()
            if len(fields) > 2 or (len(fields) == 2 and not fields[1][0].isdigit()):
                time = time.copy()
                time.attrs = dict(time.attrs)
                time.attrs['units'] = f'{unit} since {" ".join(fields[:2])}'
        return super().decode_time(time)

    def add_hindcast_info(self):
        info = self.info
        params = self.params
        dm = params['dimension_map']
        dims = info['dims']

        info['num_nodes'] = dims[dm['node']]

        if info['is3D']:
            # "level" holds layer bottoms, so there is one more interface than layer
            info['num_layers'] = dims[dm['z']]
            info['num_z_interfaces'] = info['num_layers'] + 1
            info['vert_grid_type'] = si.vertical_grid_types.Zfixed

    # horizontal grid
    # ---------------------------------------------------------
    def read_triangles(self, grid):
        params = self.params
        gm = params['grid_variable_map']
        ml = si.msg_logger

        if gm['triangles'] is not None and gm['triangles'] in self.info['variables']:
            # some SHYFEM output keeps the connectivity, use it directly
            tri = self.dataset.read_variable(gm['triangles']).data.astype(np.int32)
            grid['triangles'] = tri - int(params['one_based_indices'])
            return

        if params['grd_file_name'] is None:
            # gm['triangles'] is None when no alternative was found in the files, so name
            # the variable the reader looked for rather than the value it resolved to
            looked_for = self.default_params['grid_variable_map']['triangles'].alternatives
            ml.msg(f'SHYFEM files have no {" or ".join(chr(34) + str(v) + chr(34) for v in looked_for)} variable, '
                   f'so reader parameter "grd_file_name" '
                   f'must give the SHYFEM ".grd" grid file holding the element connectivity',
                   hint='EMERGE Adriatic hindcasts were post processed with "ncks -x -v element_index", '
                        'which strips the triangulation out of the files',
                   caller=self, fatal_error=True)
            return

        if not path.isfile(params['grd_file_name']):
            ml.msg(f'Could not find SHYFEM grd file "{params["grd_file_name"]}"', caller=self, fatal_error=True)
            return

        grd = read_grd_file(params['grd_file_name'])
        node_map, method, n_unmapped = map_grd_nodes_to_dataset_nodes(grd['x'], grid['x'])
        triangles, n_dropped = subset_triangles(grd['triangles'], node_map)

        if triangles.shape[0] == 0:
            ml.msg(f'No elements of grd file "{params["grd_file_name"]}" match the nodes of the hindcast files',
                   hint='is this the ".grd" file the hindcast was run with?', caller=self, fatal_error=True)
            return

        grid['triangles'] = triangles

        ml.progress_marker(f'Read {grd["triangles"].shape[0]} elements from SHYFEM grd file '
                           f'"{path.basename(params["grd_file_name"])}", matched to hindcast nodes by {method}')
        if n_dropped > 0:
            # normal when the hindcast is a spatial subset of the grid, eg via "cdo sellonlatbox"
            ml.msg(f'Dropped {n_dropped} of {grd["triangles"].shape[0]} grd elements which use nodes not in the hindcast files, '
                   f'keeping {triangles.shape[0]}',
                   hint='expected when the hindcast files are a spatial subset of the ".grd" grid',
                   note=True, caller=self)

        n_orphan = grid['x'].shape[0] - np.unique(triangles).size
        if n_orphan > 0:
            ml.msg(f'{n_orphan} of {grid["x"].shape[0]} hindcast nodes are in no element of the grd file and are treated as land',
                   hint='the ".grd" file may be a different revision of the grid than the one the hindcast was run with',
                   warning=True, caller=self)

    # vertical grid
    # ---------------------------------------------------------
    def build_vertical_grid(self):
        info = self.info
        grid = self.grid
        gm = self.params['grid_variable_map']

        # total water depth at nodes, needed before the water_depth field exists
        grid['total_depth'] = self.dataset.read_variable(
                                self.params['field_variable_map']['water_depth']).data.astype(np.float32)

        # depth, positive down, of the bottom of each layer, surface layer first
        layer_bottom_depth = self.dataset.read_variable(gm['z_layer_bottom']).data.astype(np.float64)
        interface_depth = np.concatenate(([0.0], layer_bottom_depth))

        # the sea bed can be deeper than the deepest layer, either because SHYFEM lets its
        # bottom layer run down to the bathymetry, or because a spatial subset of the output
        # kept the full "total_depth" while trimming the layers, eg the EMERGE 2019 files.
        # Deepen the bottom interface so the vertical grid always contains the sea bed,
        # otherwise particles below it get an out of range vertical cell.
        deepest_bed = float(np.nanmax(grid['total_depth']))
        if deepest_bed > interface_depth[-1]:
            n_below = int(np.count_nonzero(grid['total_depth'] > interface_depth[-1]))
            si.msg_logger.msg(f'The sea bed is below the deepest layer at {n_below} of {info["num_nodes"]} nodes, '
                              f'deepest layer bottom is {interface_depth[-1]:.1f} m and the deepest bed is {deepest_bed:.1f} m',
                              hint='the bottom layer is stretched down to the sea bed at those nodes',
                              note=True, caller=self)
            interface_depth[-1] = deepest_bed

        # z interfaces, as z increasing upwards from the deepest, ie OceanTracker's ordering
        grid['z'] = (-interface_depth[::-1]).astype(np.float32)
        grid['z_layer_fixed'] = (0.5 * (grid['z'][:-1] + grid['z'][1:])).astype(np.float32)

        super().build_vertical_grid()

    def read_bottom_interface_index(self, grid):
        info = self.info

        if not info['is3D']:
            return np.zeros((info['num_nodes'],), dtype=np.int32)

        # the bottom layer is the deepest layer which is both above the sea bed and holds data.
        # "total_depth" and the layer depths give the first, but not all SHYFEM output marks
        # cells below the bed with the fill value, eg some pad them with zeros instead, so the
        # deeper of the two is used to make sure no below-bed padding is ever read as a velocity
        from_depth = self._bottom_layer_index_from_depth(grid)

        u = self.read_layer_data_bottom_up(self.params['field_variable_map']['water_velocity'][0], nt=0)
        from_fill = self._first_layer_above_bottom(u[0, ...])

        bottom_layer_index = np.maximum(from_depth, from_fill).astype(np.int32)

        # the fill pattern is only usable if the files actually mark below-bed cells
        n_nodes_with_fill = int(np.count_nonzero(np.any(np.isnan(u[0, ...]), axis=1)))
        if n_nodes_with_fill < 0.5 * info['num_nodes']:
            # eg the EMERGE hindcasts declare _FillValue = -999 but pad below the bed with zeros
            si.msg_logger.msg('Files hold no fill values below the sea bed, so the bottom layer at each node '
                              'comes from "total_depth" and the layer depths',
                              note=True, caller=self)
        else:
            n_differ = int(np.count_nonzero(from_depth != from_fill))
            if n_differ > 0:
                si.msg_logger.msg(f'Bottom layer from "total_depth" and from the fill values below the bed '
                                  f'differ at {n_differ} of {info["num_nodes"]} nodes, using the shallower of the two',
                                  hint='the files may pad part of the column below the sea bed rather than filling it',
                                  note=True, caller=self)

        grid['bottom_layer_index'] = bottom_layer_index
        return bottom_layer_index  # layer n sits above interface n

    @staticmethod
    def _first_layer_above_bottom(data):
        # data is (node, layer) ordered bottom up, find the deepest layer holding a value
        n_nodes, n_layers = data.shape
        index = np.full((n_nodes,), n_layers - 1, dtype=np.int32)
        is_wet = ~np.isnan(data)
        has_any = np.any(is_wet, axis=1)
        index[has_any] = np.argmax(is_wet[has_any, :], axis=1).astype(np.int32)
        return index

    def _bottom_layer_index_from_depth(self, grid):
        # deepest layer whose top interface is above the sea bed
        info = self.info
        n_layers = info['num_layers']
        layer_top_depth = -grid['z'][1:]  # depth, positive down, of top of each layer, bottom up
        depth = grid['total_depth'][:, np.newaxis]
        is_wet = layer_top_depth[np.newaxis, :] < depth
        index = np.full((info['num_nodes'],), n_layers - 1, dtype=np.int32)
        has_any = np.any(is_wet, axis=1)
        index[has_any] = np.argmax(is_wet[has_any, :], axis=1).astype(np.int32)
        return index

    # reading data
    # ---------------------------------------------------------
    def read_layer_data_bottom_up(self, var_name, nt=None):
        """Read a (time, node, level) variable and flip the layers to OceanTracker's bottom up order."""
        data = self.dataset.read_variable(var_name, nt=nt).data
        if data.ndim == 2:
            data = data[np.newaxis, ...]
        return np.ascontiguousarray(data[:, :, ::-1], dtype=np.float32)

    def read_file_var_as_4D_nodal_values(self, var_name, var_info, nt=None):
        # read variable into 4D ( time, node, depth, comp) format
        info = self.info
        grid = self.grid
        params = self.params

        is3D = any(d in var_info['dims'] for d in params['all_z_dims'])

        if is3D:
            data = self.read_layer_data_bottom_up(var_name, nt=nt)
            # values are representative of the layer, move them onto the layer interfaces
            data = hg_trans.convert_3Dfield_fixed_z_layer_to_fixed_z_interface(
                                data, grid['z_layer_fixed'], grid['z'],
                                grid['bottom_layer_index'], grid['total_depth'])
        else:
            data = np.asarray(self.dataset.read_variable(var_name, nt=nt).data, dtype=np.float32)
            if info['time_dim'] not in var_info['dims']:
                data = data[np.newaxis, ...]
            data = data[:, :, np.newaxis]

        return data[..., np.newaxis]

    def read_dry_cell_data(self, nt_index, buffer_index):
        # SHYFEM output has no wet/dry flag, so work it out from the tide and water depth
        fields = self.fields
        grid = self.grid

        # a dry node has no water level in the files, replace it so nothing downstream sees a nan
        bed = -fields['water_depth'].data[0, :, 0, 0]
        for nb in buffer_index:
            is_nan = np.isnan(fields['tide'].data[nb, :, 0, 0])
            fields['tide'].data[nb, is_nan, 0, 0] = bed[is_nan] + 0.05

        reader_util.set_dry_cell_flag_from_tide(grid['triangles'], fields['tide'].data, fields['water_depth'].data,
                                                si.settings.minimum_total_water_depth,
                                                grid['is_dry_cell_buffer'], buffer_index)


# SHYFEM ".grd" grid files
# ---------------------------------------------------------
# The ".grd" format is plain text, whitespace separated, one item per line.
# The first number on a line is the item type:
#
#     0  comment
#     1  node     :  1 <node_number> <node_type> <x> <y> [<depth>]
#     2  element  :  2 <elem_number> <elem_type> <n_vertices> <node_1> .. <node_n> [<depth>]
#     3  line     :  3 <line_number> <line_type> <n_nodes> <node_1> .. <node_n> [<depth>]
#
# Long items wrap onto continuation lines, which start with whitespace.  Node
# *numbers* are arbitrary labels and are usually neither contiguous nor sorted,
# so elements/lines refer to node numbers which must be mapped to node indices.

def read_grd_file(file_name):
    """Read a SHYFEM ".grd" file.

    Returns dict with
        x                 (n_nodes,2) float64 node coords, in file order
        node_numbers      (n_nodes,)  int64 node label of each node
        node_types        (n_nodes,)  int32
        node_depth        (n_nodes,)  float64, nan where not given
        triangles         (n_tri,3)   int32 indices into "x" (zero based)
        element_numbers   (n_tri,)    int64
        element_depth     (n_tri,)    float64, nan where not given
        lines             list of dict(number=, type=, nodes=int32 indices)
        n_non_triangular_elements  int, elements with != 3 vertices (skipped)
    """
    node_numbers, node_types, nx, ny, node_depth = [], [], [], [], []
    elements, element_numbers, element_depth = [], [], []
    lines = []
    n_non_tri = 0

    for item in _iter_items(file_name):
        item_type = int(item[0])

        if item_type == 1:
            # 1 <node_number> <node_type> <x> <y> [<depth>]
            node_numbers.append(int(item[1]))
            node_types.append(int(item[2]))
            nx.append(float(item[3]))
            ny.append(float(item[4]))
            node_depth.append(float(item[5]) if len(item) > 5 else np.nan)

        elif item_type == 2:
            # 2 <elem_number> <elem_type> <n_vert> <node_1..n> [<depth>]
            n_vert = int(item[3])
            nodes = [int(v) for v in item[4:4 + n_vert]]
            if n_vert != 3:
                n_non_tri += 1
                continue
            element_numbers.append(int(item[1]))
            elements.append(nodes)
            element_depth.append(float(item[4 + n_vert]) if len(item) > 4 + n_vert else np.nan)

        elif item_type == 3:
            # 3 <line_number> <line_type> <n_nodes> <node_1..n> [<depth>]
            n_nodes = int(item[3])
            lines.append(dict(number=int(item[1]), type=int(item[2]),
                              node_numbers=np.asarray([int(v) for v in item[4:4 + n_nodes]], dtype=np.int64)))
        # item_type 0 (comment) and anything else is ignored

    grd = dict(
        x=np.stack((np.asarray(nx, dtype=np.float64), np.asarray(ny, dtype=np.float64)), axis=1),
        node_numbers=np.asarray(node_numbers, dtype=np.int64),
        node_types=np.asarray(node_types, dtype=np.int32),
        node_depth=np.asarray(node_depth, dtype=np.float64),
        element_numbers=np.asarray(element_numbers, dtype=np.int64),
        element_depth=np.asarray(element_depth, dtype=np.float64),
        n_non_triangular_elements=n_non_tri,
    )

    # map node numbers used by elements/lines to zero based node indices
    node_number_to_index = _build_node_number_lookup(grd['node_numbers'])

    if len(elements) == 0:
        grd['triangles'] = np.zeros((0, 3), dtype=np.int32)
    else:
        tri = node_number_to_index[np.asarray(elements, dtype=np.int64)]
        if np.any(tri < 0):
            bad = int(np.count_nonzero(np.any(tri < 0, axis=1)))
            raise ValueError(f'SHYFEM grd file "{file_name}" has {bad} elements referring to undefined node numbers')
        grd['triangles'] = tri.astype(np.int32)

    for line in lines:
        line['nodes'] = node_number_to_index[line['node_numbers']].astype(np.int32)
    grd['lines'] = lines

    return grd


def _iter_items(file_name):
    """Yield each ".grd" item as a list of string fields, re-joining continuation lines.

    A line starting with whitespace continues the previous item, a blank line ends it.
    """
    item = []
    with open(file_name, 'r') as f:
        for raw in f:
            stripped = raw.strip()
            if stripped == '':
                if item:
                    yield item
                    item = []
                continue
            if raw[0].isspace() and item:
                item += stripped.split()  # continuation of current item
                continue
            if item:
                yield item
            item = stripped.split()
    if item:
        yield item


def _build_node_number_lookup(node_numbers):
    # node numbers are arbitrary labels, build number -> index lookup table
    lut = np.full(int(node_numbers.max()) + 1, -1, dtype=np.int64)
    lut[node_numbers] = np.arange(node_numbers.size, dtype=np.int64)
    return lut


def map_grd_nodes_to_dataset_nodes(grd_x, dataset_x, tol=1.0e-4):
    """Map ".grd" node indices onto the node indices of the hindcast files.

    Two edge cases occurred in practice:

    * the hindcast holds the whole model grid, and the node order is identical
      to the ".grd" (possibly with a handful of nodes added/moved in a later
      grid revision)  ->  "positional" mapping,
    * the hindcast is a spatial subset (eg made by "cdo sellonlatbox"), which
      renumbers and reorders nodes  ->  "coordinate" mapping.

    Returns (node_map, method, n_unmapped) where node_map[i] is the dataset
    node index of ".grd" node i, or -1 if that node is not in the dataset.
    """
    grd_x = np.asarray(grd_x, dtype=np.float64)
    dataset_x = np.asarray(dataset_x, dtype=np.float64)
    n_grd, n_dataset = grd_x.shape[0], dataset_x.shape[0]

    # try a straight positional match first, it is exact when it applies
    n = min(n_grd, n_dataset)
    offset = np.abs(grd_x[:n, :] - dataset_x[:n, :]).max(axis=1)
    if n > 0 and np.count_nonzero(offset <= tol) > 0.99 * n:
        node_map = np.arange(n_grd, dtype=np.int64)
        node_map[n:] = -1  # grd has nodes the dataset does not
        return node_map, 'positional', int(np.count_nonzero(node_map < 0))

    # otherwise match on nearest coordinate within tolerance.  An exact match cannot
    # be used, the ".grd" holds 6 decimal text while the files hold float32, which only
    # has ~7 significant digits, so the two disagree in the last digit for many nodes.
    from scipy.spatial import cKDTree
    dist, index = cKDTree(dataset_x).query(grd_x, k=1, distance_upper_bound=tol)
    node_map = np.where(np.isfinite(dist), index, -1).astype(np.int64)

    return node_map, 'coordinate', int(np.count_nonzero(node_map < 0))


def subset_triangles(triangles, node_map):
    """Re-index ".grd" triangles onto dataset nodes, dropping any triangle with an unmapped node."""
    tri = node_map[np.asarray(triangles, dtype=np.int64)]
    keep = np.all(tri >= 0, axis=1)
    return tri[keep, :].astype(np.int32), int(np.count_nonzero(~keep))
