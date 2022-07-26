import numpy as np
from numba import njit
from numba.typed import List as NumbaList
from oceantracker.util.polygon_util import InsidePolygon
from oceantracker.util import  basic_util



# build node to cell map
@njit
def build_node_to_cell_map(tri,x):
    # build list  giving map from each node to list of cells which contain that node

    n_nodes = x.shape[0]
    # make empty list for each node
    node_to_tri_map = NumbaList()
    for n in range(n_nodes):
        node_to_tri_map.append(NumbaList([np.int32(0)]))
        del node_to_tri_map[-1][-1]  # make it empty

    #  build a node to triangles map
    for nTri  in range(tri.shape[0]):
        for m  in range(tri.shape[1]):
            node = tri[nTri,m]
            # log one more triangle for this node
            node_to_tri_map[node].append(np.int32(nTri))

    return node_to_tri_map

# build adjacency matrix from node to triangles map
@njit
def build_adjacency_from_node_cell_map(node_to_tri_map, tri):
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
            for tri1 in node_to_tri_map[n1]:
                if tri1 == nTri: continue # don't search if same as current tri

                # search triangles of second node
                for tri2 in node_to_tri_map[n2]:
                    if tri2 == nTri:
                        continue  # don't find current triangle
                    elif tri2 == tri1:
                        in_common = tri2  # triangle in common to both nodes' to tri lists
                        break

                if in_common != -1 : break # found, so stop looking

            if in_common != -1:
                adjacency[nTri, m] = in_common

    return  adjacency

def get_boundary_triangles(adjacency_matrix):
    # true false for boundary triangles
    nedges = np.sum(adjacency_matrix == -1, axis=1)
    boundary_tri = np.logical_and(nedges > 0, nedges < 3)
    return boundary_tri

def build_grid_outlines(triangles,adjacency_matrix,x, node_triangle_map):

    @njit
    def build_edge_node_pairs(triangles, adjacency_matrix, boundary_tri):

        # find triangles with edges ( but not those with 3 edges, which are not connected to the domain)


        edge_node_pairs = np.full((2*boundary_tri.shape[0],2), -100, dtype=np.int32) # space for maximum number of edges at 1 or 2 per triangle

        nfound = 0  # number of pairs found
        for n in boundary_tri:
            # 1 or 2 edges
            for ne in np.flatnonzero(adjacency_matrix[n,:] == -1):
                for nn in np.arange(2):
                    edge_node_pairs[nfound,nn] = triangles[n,(ne+1+nn) % 3 ]
                nfound +=1

        return edge_node_pairs[:nfound,:]

    @njit
    def join_segments(edge_node_pairs):
        # join segments into lines based on common nodes in edge pairs of nodes

        npairs =edge_node_pairs.shape[0]
        active = np.full((npairs,),True)# those which still need to be paired
        # make empty segment_list
        segment_list = []

        # make one segment
        while np.sum(active) > 0:
            n1 = np.argmax(active) # first active segment
            seg = [edge_node_pairs[n1,0], edge_node_pairs[n1,1] ]
            active[n1] = False # dont serach within current segment
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
                # add if 3 or more segmentss
                segment_list.append(seg)

        return segment_list

    # build pairs of edge nodes from boundary triangles
    boundary_tri= np.flatnonzero(get_boundary_triangles(adjacency_matrix))
    edge_node_pairs = build_edge_node_pairs(triangles, adjacency_matrix, boundary_tri)

    # join segments into continuous lines
    segs = join_segments(edge_node_pairs)

    # use first segment to work out if an island
    out= {'domain' : {},'islands':[]}
    for s in segs:
        nodes=np.asarray(s).astype(np.int32)

        # find tri containing first segment
        tri1 = node_triangle_map[s[0]]
        tri2 = node_triangle_map[s[1]]
        ntri= list(set(tri1) & set(tri2))[0] # triangle in common to both nodes
        x1= np.mean(x[triangles[ntri,:],:],axis=0)  # mid point of tri holding first segment
        points = x[s, :]
        poly=InsidePolygon(points)

        face_nodes= np.stack((nodes[:-1],nodes[1:]), axis=1)
        # if midpoint inside then it is not an island
        if not poly.is_inside(x1)[0]:
            out['islands'].append({'nodes': nodes, 'points': points, 'face_nodes': face_nodes})
        else:
            out['domain'].update({'nodes': nodes, 'points': points, 'face_nodes': face_nodes})
    return out

def mark_open_boundary_faces_in_adjacency_matrix(tri, boundary_triangles, boundary_nodes, adjacency_matrix):

    for ntri in np.flatnonzero(boundary_triangles):

        for nodes in boundary_nodes:
            a=1



    return adjacency_matrix


def split_quad_cells(triangles):
    # those with 4 cols are quad elements, so split into triangles
    # eg can be in schism quad cells, or regular grid viewed as triangles
    if triangles.shape[1] == 4:
        # split quad grids buy making new triangles
        sel = triangles[:, 3] > 0
        if sel.shape[0] > 0:
            triangles_to_split= np.flatnonzero(sel)  # needed when loading triangle properties, eg dry cells if used

            qtri = triangles[sel, :]  # those with 4 columns

            triangles = np.vstack((triangles[:, :3], qtri[:, [0, 2, 3]]))

    else:
        triangles_to_split = None
    return triangles, triangles_to_split

def calcuate_triangle_areas(xy, tri):
    x= xy[tri,0]
    y = xy[tri,1]
    area = 0.5 * np.abs((x[:, 0] * (y[:, 1] - y[:, 2])) + (x[:, 1] * (y[:, 2] - y[:, 0])) + (x[:, 2] * (y[:, 0] - y[:, 1])))
    return area

def convert_face_to_nodal_values(x, tri, face_data):
    # convert face values to nodal using inverse distance weight to face values of triangles surrounding each node
    @njit
    def inverse_distance_weight_face_values(node_map,x,xtri, data):
        out= np.full((len(node_map),), np.nan)

        for node in np.arange(out.shape[0]):

            if len(node_map[node]) == 0:
                out[node] = np.nan
            else:
                c, sum_data, sum_s =0, 0., 0.
                for m in np.arange(len(node_map[node])):
                    t = node_map[node][m]
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

    node_to_tri_map = build_node_to_cell_map(tri, x)
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