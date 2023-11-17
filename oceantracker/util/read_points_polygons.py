# read points or polygons from a file
import xml.etree.ElementTree as ET
import numpy as np
from oceantracker.util import  cord_transforms
def read_polygons_KML(fn, EPSG= None):
    tree = ET.parse(fn)
    root = tree.getroot()
    vtag= root.tag.split('}')[0] +'}'

    polygon_list=[]
    for child in root.findall(".//" + vtag + 'coordinates'):

        ll = np.fromstring(child.text.strip(child.tail).replace(',', ' '),sep=' ')
        ll = ll.reshape(( int(ll.size / 3), 3))[:, :2]
        if EPSG is not None:
            ll = cord_transforms.convert_cords(ll, cord_transforms.ID_WGS84,EPSG)

        polygon_list.append(dict(points= ll))

    return polygon_list