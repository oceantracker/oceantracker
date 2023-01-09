from urllib.request import urlopen
import xml.etree.ElementTree as ET
#import xmltodict
from oceantracker.util.ncdf_util import NetCDFhandler
import numpy as np
import matplotlib.pyplot as plt

class ThreddsServer(object):
    def __init__(self,base_url):
        self.base_url= base_url

        document = urlopen(base_url+'catalog.xml').read()
        self.root = ET.fromstring(document)
        self.name_space = self.root.tag.split('catalog')[0]
        pass

    def get_files(self,file_mask):
        m = file_mask.split('*')
        link=[]
        for d in self.datasets:
            ID= d.attrib['ID']
            if ID.startswith(m[0]) and ID.endswith(m[1]):
                link.append(ID)

    def get_catalog_info(self): return self._get_catalog_info(self.root)

    def get_file_list(self, file_mask=None):
        info = self.get_catalog_info()

        out = []
        if file_mask is None:
            m=['','']
        else:
            m= file_mask.split('*')


        for d in info['dataset']:
            if 'urlPath' in d:

                url = self.base_url.split('thredds')[0][:-1] +  info['service']['httpService']['base'] + d['urlPath']
                file_name= url.split('/')[-1]

                if file_name.startswith(m[0]) and file_name.endswith(m[-1]):
                    out.append(d)
                    out[-1]['url'] = url
        return out

    @staticmethod
    def _get_catalog_info(root,out=None):
        if out is None: out = {'catalogRef': [], 'dataset': [], 'service': {}}
        name_space = root.tag.split('catalog')[0]

        for child in root.iter():
            if name_space +'catalogRef' in child.tag:
                out['catalogRef'].append(_strip_namespace_from_keys(child.attrib))

            elif name_space + 'dataset' in child.tag:
                out['dataset'].append(_strip_namespace_from_keys(child.attrib))
            elif name_space + 'service' in child.tag:
                if 'name' in child.attrib:
                    out['service'][child.attrib['name']]=child.attrib
        return out

def _strip_namespace_from_keys(d):
    out={}
    for key, item in d.items():
        new_key= key.split('}')[-1] if '}' else key
        out[new_key] = item
    return out



if __name__ == "__main__":

    # dev testing
    # /thredds/fileServer/NOAA/LSOFS/MODELS/2023/01/06/nos.lsofs.fields.n002.20230106.t00z.nc
   #'https://opendap.co-ops.nos.noaa.gov/'
    base_url = 'https://www.ncei.noaa.gov/'
    et = ThreddsServer(base_url + 'thredds/catalog/NOAA/LSOFS/MODELS/2023/01/01/')
    out=et.get_file_list(file_mask='nos.lsofs.fields*.nc')

    for o in out:
        url= urlopen(o['url'])
        nc= NetCDFhandler(url)
        pass


