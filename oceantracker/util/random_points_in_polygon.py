from scipy.spatial import Delaunay
import numpy as np
from matplotlib import pyplot as plt
# under development
class PointsInPolygonByTriangulation(object):
    def __init__(self, x):
        D = Delaunay(x)
        self.x = D.points
        self.tri = D.simplices.copy()
        pass


if __name__ == '__main__':
    poly_points = [[1597682.1237, 5489972.7479],
                   [1598604.1667, 5490275.5488],
                   [1598886.4247, 5489464.0424],
                   [1597917.3387, 5489000],
                   [1597300, 5489000], [1597682.1237, 5489972.7479]]


    x= np.asarray( poly_points)[:,:2]

    pt= PointsInPolygonByTriangulation(x)

    plt.triplot(pt.x[:,0],pt.x[:,1], pt.tri)
    plt.plot(x[:,0],x[:,1],'g')
    plt.show()