import numpy as np

import fiona
from os import  path


def ReadCoordinates(file_name, type, select_entity, msg_logger,crumbs, only_select_one=False):
    # get given types selected groups of entity types=[;line','polygon','points']

    out= []
    # read file
    if not path.isfile(file_name):
        msg_logger.msg(f'cannot file {"file_name"}' ,
               hint='Check path and name',
               fatal_error= True,
               crumbs='Pre processing > ReadCoordinates')
    try:
        d= fiona.open(file_name)
    except Exception as e:
        msg_logger.msg(f'cannot read file {file_name} ', hint='File tyype not recognised by "fiona" module',
               fatal_error=True, crumbs='Pre processing > ReadCoordinates')

    for item in d:
        g = item['geometry']
    xy = np.asarray(g['coordinates'])
    if 'multi' in g['type'].lower():
        # flatten first two dim
        xy = xy.reshape(((xy.shape[0]*xy.shape[1],)+ xy.shape[2:]))
    for row in range(xy.shape[0]):
        i={'points' : xy[row,:,:],'name': f'{item.id}_{row:03}'}
        if type in g['type'].lower():
            out.append(i)

    msg_logger.progress_marker(f'Read user coordinates from file "{file_name}" ')
    msg_logger.progress_marker(f'found {len(out):d} {type}', tabs=2)


    if select_entity is None:
        if only_select_one:
            msg_logger.msg(f'Can only select one entity of type from coordinates file {file_name}, must use parameter select_entities ', hint='eg.  use parameter select_entities =0',
                           fatal_error=True, crumbs=crumbs+ 'Reading coordinates from file')
            out =out # return  all
        # get all, put merger points into single entity
        if type=='points':
            pass
    else:
        # select given entity amost groups in file
        if type(select_entity) != list: select_entity= [select_entity]
        if only_select_one and len(select_entity) > 1:
            msg_logger.msg(f'Can only select one entity of type from coordinates file {file_name}', hint='eg.  use parameter select_entities =0',
                           fatal_error=True, crumbs=crumbs + 'Reading coordinates from file')
        out = out[select_entity]

    return  out








