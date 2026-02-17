import numpy  as np
from oceantracker.util.parameter_checking import ParameterCoordsChecker as PCC, ParamValueChecker as PVC, ParameterListChecker as PLC
from oceantracker.shared_info import shared_info as si

def add_grid_default_params(default_params,is3D=False,grid_center_required=True):

    default_params.update(
        rows = PVC(100, int,  min=1, max=10 ** 5,
                   doc_str='Number of rows in grid (y direction)'),
        cols = PVC(98, int, min=1, max=10 ** 5,
                   doc_str='Number of columns in grid (x direction)'),
        span_x = PVC(100000., float,  doc_str='Grid span  in x direction',
                    units='Units metres or degrees if hindcast is geographic coords'),
        span_y = PVC(100000., float, doc_str='Grid span  in y direction',
                   units='Metres or degrees if hindcast in geographic coords'),
        grid_center= PCC(None, single_cord=True, is3D=False,is_required=grid_center_required,
                           doc_str='center of the statistics grid as (x,y), must be given if not using  release_group_centered_grids',
                           units='Metres or degrees if hindcast in geographic coords'),
        grid_size= PLC(None, int, fixed_len=2, min=1, max=10 ** 5, deprecated=True,
                    doc_str='deprecated: use parameters rows=??,cols=?? '),
        grid_span=PLC(None, float, units='meters (dx,dy)', deprecated=True,
                      doc_str='deprecated: use span_x=? and span_y=? params)'),
        )

    if is3D:
        default_params.update(layers = PVC(10, int, min=1, max=10 ** 5, doc_str='number of layers in 3D grid'),
        grid_size=PLC(None, int, fixed_len=3, min=1, max=10 ** 5, deprecated=True,
                        doc_str='number of (rows, columns,layers) in grid, (deprecated: use parameters rows=??,cols=??, layers=?? )'),
            )


def build_grid_from_params(params,caller, center=None):
    ml = si.msg_logger
    if center is   None: center= params['grid_center']  # allow center param to be overridden ( eg gridded stats)

    # use deprecated params if given
    if len(params['grid_size']) > 0:
        params['rows'], params['cols'] = params['grid_size'][0], params['grid_size'][1]
        if len(params['grid_size']) == 3: params['layers'] = params['grid_size'][2]
    if len(params['grid_span']) > 0:
        params['span_x'], params['span_y'] = params['grid_span'][0], params['grid_span'][1]



    # test if grid span too big or too small for geographic or meter grids if si.run_info.
    if si.settings.use_geographic_coords and  max(params['span_x'],params['span_y'] ) > 360 :
        ml.msg('Using geographic coords, but param span_x or span_y > 360 ', error=True,caller=caller,
               hint='Using meters, should be  degrees?')

    if not si.settings.use_geographic_coords and min(params['span_x'],params['span_y'] ) < 360:
        ml.msg('Using meters grid but but param span_x or span_y  < 360 ', strong_warning=True,caller=caller,
               hint='very small grid or mistakenly using spans in degrees , should be in meters?')

    base_x =  np.linspace(-params['span_x'] / 2., params['span_x'] / 2., params['cols']+1).reshape(-1, 1)
    base_y =  np.linspace(-params['span_y'] / 2., params['span_y'] / 2., params['rows']+1).reshape(-1, 1)
    xi, yi = np.meshgrid(center[0]+base_x, center[1]+ base_y)

    return xi, yi, get_bounding_box(xi, yi)

def get_bounding_box(x_grid,y_grid):
    bounding_box_ll_ul = np.asarray([[x_grid[0, 0], y_grid[0, 0]], [x_grid[0, -1], y_grid[-1, 0]]], dtype=np.float64)
    return bounding_box_ll_ul