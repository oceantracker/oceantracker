import numpy as np
from numba import njit, prange
from numba.typed import List as NumbaList
from oceantracker.util.polygon_util import InsidePolygon
from oceantracker.util import  basic_util
from oceantracker.util.numba_util import njitOT


# build node to cell map
@njitOT
def build_node_to_triangle_map(tri, x):
    # build list  giving map from each node to list of cells which contain that node

    # make empty array with guess of how many triangles per node
    # using arrays faster than appending to lists
    # need to expand array if needed to aviod crash
    n_block = 10
    empty_block = np.full((x.shape[0],n_block), -1, dtype=np.int32)
    node_to_tri_map =empty_block.copy()

    tri_per_node = np.full((x.shape[0],), 0, dtype=np.int32)
    max_cells_per_node = 0

    #  build a node to triangles map

    for nTri  in range(tri.shape[0]):
        for m  in range(3):
            node = tri[nTri, m]
            tri_per_node[node] += 1
            max_cells_per_node = max(tri_per_node[node], max_cells_per_node)

            # if not enough space add columns to matrix
            if tri_per_node[node] >= node_to_tri_map.shape[1]:
                # add another block
                node_to_tri_map = np.concatenate((node_to_tri_map, empty_block.copy()),axis=1)

            # log one more triangle for this node
            node_to_tri_map[node, tri_per_node[node]-1] = nTri

    return node_to_tri_map, tri_per_node

# build adjacency matrix from node to triangles map
@njitOT
def build_adjacency_from_node_tri_map(node_to_tri_map, tri_per_node, tri):
    # build adjacency matrix for use in triangle walk and as lateral boundary of model
    adjacency = np.full(tri.shape, -1, dtype=np.int32)

    # now look for intersection of sets of triangles  for nodes in same face to get adjacent triangles
    for nTri in range(tri.shape[0]):
        for m in range(tri.shape[1]):
            # get node numbers for face opposite node tri[case,m]
            n1  = tri[nTri, (m + 1) % 3]
            n2  = tri[nTri, (m + 2) % 3]

            # find intersection of triangle sets for nodes n1, n2
            in_common = -1
            for tri1 in node_to_tri_map[n1,:tri_per_node[n1]]:
                if tri1 == nTri: continue # don't search if same as current tri

                # search triangles of second node
                for tri2 in node_to_tri_map[n2,:tri_per_node[n2]]:
                    if tri2 == nTri:
                        continue  # don't find current triangle
                    elif tri2 == tri1:
                        in_common = tri2  # triangle in common to both nodes' to tri lists
                        break

                if in_common != -1 : break # found, so stop looking

            if in_common != -1:
                adjacency[nTri, m] = in_common

    return adjacency

def get_boundary_triangles(adjacency_matrix):
    # true false for boundary triangles where adjacency < 0
    return np.any(adjacency_matrix < 0, axis=1).astype(np.int8)

def build_grid_outlines(triangles, adjacency,is_boundary_triangle,node_to_tri_map,x):

    @njitOT
    def build_edge_node_pairs(triangles, adjacency_matrix, boundary_tri):

        # find triangles with edges ( but not those with 3 edges, which are not connected to the domain)
        edge_node_pairs = np.full((2*boundary_tri.shape[0],2), -100, dtype=np.int32) # space for maximum number of edges at 1 or 2 per triangle

        nfound = 0  # number of pairs found
        for n in boundary_tri:
            # 1 or 2 edges
            for ne in np.flatnonzero(adjacency_matrix[n,:] == -1):
                for nn in np.arange(2):
                    edge_node_pairs[nfound,nn] = triangles[n,(ne+1+nn) % 3 ]
                nfound += 1

        return edge_node_pairs[:nfound,:]

    @njitOT
    def join_segments(edge_node_pairs):
        # join segments into lines based on common nodes in edge pairs of nodes
        # todo this is slow try with exapanding numpy array
        npairs =edge_node_pairs.shape[0]
        active = np.full((npairs,),True)# those which still need to be paired
        # make empty segment_list
        segment_list = []

        # make one segment
        while np.sum(active) > 0:
            n1 = np.argmax(active) # first active segment
            seg = [edge_node_pairs[n1,0], edge_node_pairs[n1,1] ]
            active[n1] = False # dont search within current segment
            segment_ended= False

            while not segment_ended:
                to_search = np.flatnonzero(active)
                next_node = -1
                for nseg in to_search:
                    if  edge_node_pairs[nseg,0] ==seg[-1] :
                        next_node = edge_node_pairs[nseg,1] # other node added to s
                        active[nseg] = False
                        break
                    elif edge_node_pairs[nseg,1] ==seg[-1]:
                        next_node = edge_node_pairs[nseg,0]
                        active[nseg] = False
                        break

                if next_node ==-1:
                    segment_ended=True #
                else:
                    seg.append(next_node)

            if len(seg) >= 3:
                # add if 3 or more segments
                segment_list.append(seg)

        return segment_list

    # build pairs of edge nodes from boundary triangles
    #t0= perf_counter()
    edge_node_pairs = build_edge_node_pairs(triangles, adjacency, np.flatnonzero(is_boundary_triangle==1))
    #print('build_edge_node_pairs',perf_counter()-t0)

    # join segments into continuous lines
    #t0 = perf_counter()
    segs = join_segments(edge_node_pairs)
    #print('join_segments', perf_counter() - t0)

    # work out if an island or domain and unpack data
    out= {'domain' : {},'islands':[]}
    len_seg = [len(l) for l in segs] # f

    # split segments into  domain or island
    # domain is line segment containing most easterly node in the trangulation
    nodes=np.unique(triangles)
    x_tri =  x[ nodes, 0]
    domain_node= nodes[np.argmax( x_tri == x_tri.min())]

    for s in segs:
        nodes=np.asarray(s).astype(np.int32)
        points = x[s, :]
        #face_nodes= np.stack((nodes[:-1],nodes[1:]), axis=1)
        #d = {'nodes': nodes, 'points': points, 'face_nodes': face_nodes}
        d = {'nodes': nodes, 'points': points}
        # longest segment must be the domain
        if domain_node in nodes :
            out['domain'].update(d)
        else:
            out['islands'].append(d)
    return out

def calcuate_triangle_areas(xy, tri):
    x= xy[tri,0]
    y = xy[tri,1]
    area = 0.5 * np.abs((x[:, 0] * (y[:, 1] - y[:, 2])) + (x[:, 1] * (y[:, 2] - y[:, 0])) + (x[:, 2] * (y[:, 0] - y[:, 1])))
    return area

def convert_face_to_nodal_values(x, tri, face_data):
    # convert face values to nodal using inverse distance weight to face values of triangles surrounding each node
    @njitOT
    def inverse_distance_weight_face_values(node_map,x,xtri, data):
        out = np.full((len(node_map[0]),), np.nan)

        for node in np.arange(out.shape[0]):

            if node_map[1][node] == 0:
                out[node] = np.nan
            else:
                c, sum_data, sum_s = 0, 0., 0.
                for m in np.arange(node_map[1][node]):
                    t = node_map[0][node][m]
                    if ~np.isnan(data[t]):
                        s= 1./np.sqrt( (x[node,0]-xtri[t,0])**2 + (x[node,1]-xtri[t,1])**2)
                        sum_data +=  data[t]*s
                        sum_s += s
                        c += 1
                if c > 0:
                    out[node] = sum_data/sum_s # use first as a test
                else:
                    out[node] = np.nan
        return out

    node_to_tri_map = build_node_to_triangle_map(tri, x)
    xtri = np.concatenate((np.mean(x[tri, 0], 1).reshape(-1, 1), np.mean(x[tri, 0], 1).reshape(-1,1)), axis=1)

    if face_data.size==1:
        data_nodes = inverse_distance_weight_face_values(node_to_tri_map, x, xtri,  face_data)
    else:
        # data is (time, face)
        nt =face_data.shape[0]
        data_nodes= np.full(( nt ,x.shape[0]), np.nan)
        for n in range(nt):
            data_nodes[n,:]=inverse_distance_weight_face_values(node_to_tri_map, x, xtri,  face_data[n,:])
    return data_nodes

def split_quad_cells(triangles_and_quads,quad_cells_to_split):
    # find indices flagged by boolean for splitting
    # put split cell info next to each other which mayu speed accesing getting nodal data from memory due to caching
    if quad_cells_to_split is not None:
        qtri = triangles_and_quads[quad_cells_to_split, :] # quad simplex for those to split
        new_tri =  qtri[:, [0, 2, 3]] # build simplex for split triangles
        triangles = np.concatenate((triangles_and_quads[:,:3],new_tri), axis=0)
    return triangles

@njitOT
def get_quad_nodes(shape):
    # get four nodes for each cell in regular grid of given shape
    cols, rows = shape
    def array_index(r, c):  return cols * r + c

    quad_cells = np.full(( (rows-1)*(cols-1), 4),-1,dtype=np.int32)
    n = 0
    for r in range(rows-1):
        for c in range(cols - 1):
            quad_cells[n, 0] = array_index(r,c)
            quad_cells[n, 1] = array_index(r, c+1)
            quad_cells[n, 2] = array_index(r+1, c + 1)
            quad_cells[n, 3] = array_index(r + 1, c )
            n +=1
    return quad_cells

if __name__ == "__main__":
    # testing and timing of above routines
    from oceantracker.util import ncdf_util
    from matplotlib import pyplot as plt
    from oceantracker.util import message_logger
    from time import perf_counter
    fn = 'G:\\Hindcasts_large\\MalbroughSounds_10year_benPhD\\2008\\schism_marl20080101_00z_3D.nc'
    nc = ncdf_util.NetCDFhandler(fn)
    x= nc.read_a_variable('SCHISM_hgrid_node_x')
    y = nc.read_a_variable('SCHISM_hgrid_node_y')
    xy = np.stack((x, y), axis=1)
    tri = nc.read_a_variable('SCHISM_hgrid_face_nodes') -1

    msg = messgage_logger.MessageLogger('tri util timing')

    t0 = perf_counter()
    tri = split_quad_cells(tri,tri[:,3] >=0)
    msg.progress_marker('split quad cells', start_time=t0)

    t0 = perf_counter()
    node_to_tri_map, tri_per_node = build_node_to_triangle_map(tri, xy)
    msg.progress_marker('split node_to_cell_map cells', start_time=t0)


    t0 = perf_counter()
    adjacency = build_adjacency_from_node_tri_map(node_to_tri_map, tri_per_node, tri)
    msg.progress_marker('build_adjacency_from_node_cell_map', start_time=t0)

    is_boundary_triangle = get_boundary_triangles(adjacency)

    t0 = perf_counter()
    outlines = build_grid_outlines(tri, adjacency, is_boundary_triangle, node_to_tri_map, xy)
    msg.progress_marker('grid_outlines', start_time=t0)


    plt.triplot(x,y,tri,c=[.8,.8,.8],lw=.5)
    plt.triplot(x, y, tri[is_boundary_triangle,:]==1, c=[.2, .2, .5],lw=.5)

    plt.plot(outlines['domain']['points'][:,0],outlines['domain']['points'][:,1],c=[.9,.1,.1])
    for i in outlines['islands']:
        plt.plot(i['points'][:, 0], i['points'][:, 1], c=[.1,.9,  .1])
    plt.show()

    pass

@njitOT
def get_quad_nodes(shape):
    # get four nodes for each cell in regular grid of given shape
    cols, rows = shape
    def array_index(r, c):  return cols * r + c

    quad_cells = np.full(( (rows-1)*(cols-1), 4),-1,dtype=np.int32)
    n = 0
    for r in range(rows-1):
        for c in range(cols - 1):
            quad_cells[n, 0] = array_index(r,c)
            quad_cells[n, 1] = array_index(r, c+1)
            quad_cells[n, 2] = array_index(r+1, c + 1)
            quad_cells[n, 3] = array_index(r + 1, c )
            n +=1
    return quad_cells

