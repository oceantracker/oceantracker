from urllib.request import urlopen
import xml.etree.ElementTree as ET
#import xmltodict
import netCDF4
import numpy as np
import matplotlib.pyplot as plt

class ThreddsServer(object):
    def __init__(self,base_url):
        self.base_url= base_url

        document = urlopen(base_url+'catalog.xml').read()

        self.root = ET.fromstring(document)
        self.name_space = self.root.tag.split('catalog')[0]

        for child in self.root.iter():
            print(child,child.attrib)
        self.get_catalog_info()
        pass
    def get_files(self,file_mask):
        m = file_mask.split('*')
        link=[]
        for d in self.datasets:
            ID= d.attrib['ID']
            if ID.startswith(m[0]) and ID.endswith(m[1]):
                link.append(ID)
    def get_catalog_info(self): self._get_catalog_info(self.root)

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
                #data = dataset['dataset']
                #if type(data) != list: data = [data]
                #for i in data:
                 #   out['dataset'].append(i['@ID'])

            print(child, child.attrib)
        d = get_catalog(url)
        dataset = d['catalog']['dataset']
        s = {}
        for item in d['catalog']['service']['service']:
            s[item['@name']] = item['@base']

        if 'catalogRef' in dataset:
            data = dataset['catalogRef']
            if type(data) != list: data = [data]
            for i in data:
                out['catalogRef'].append(i['@ID'])
        if 'dataset' in dataset:
            data = dataset['dataset']
            if type(data) != list: data = [data]
            for i in data:
                out['dataset'].append(i['@ID'])

def _strip_namespace_from_keys(d):
    out={}
    for key, item in d.items():
        new_key= key.split('}')[-1] if '}' else key
        out[new_key] = item
    return out

def get_catalog(url,catalog_file=None):
    if catalog_file is None: catalog_file='catalog'

    file = urlopen(url+ catalog_file+ '.xml')
    data = file.read()
    d = xmltodict.parse(data)
    return d


def walk_url(url_base,catalog_path,file_mask,out = None):
    # walk through url tree to fine all data sets matching file mask

    catalog = get_catalog_data_sets(url_base+catalog_path)
    if out is None:
        out={'url_base': url_base, 'services': catalog['service'] ,'files':[],'http':[]}

    for  c in catalog['catalogRef']:
        # walk next deeper level
        out= walk_url(url_base, c +'/', file_mask,out = out)

    m=file_mask.split('*')
    for f in catalog['dataset']:
        fn = f.split('/')[-1]
        if fn.startswith(m[0]) and fn.endswith(m[1]):
            out['files'].append(f)
            for name,s in out['services'].items():
                nn= name.split('Service')[0]
                if nn not in out : out[nn]=[]
                out[nn].append(out['url_base']+ out['services'][name]+f)

    return out

if __name__ == "__main__":

    # dev testing
    # /thredds/fileServer/NOAA/LSOFS/MODELS/2023/01/06/nos.lsofs.fields.n002.20230106.t00z.nc
    base_url=  'https://opendap.co-ops.nos.noaa.gov/'

    et = ThreddsServer(base_url + 'thredds/catalog/NOAA/LSOFS/MODELS/2023/01/01/')

    l= walk_url(base_url,'thredds/catalog/NOAA/LSOFS/MODELS/2023/01/01/','nos.lsofs.fields*.nc',out = None)

    url=l['dap'][0]

    nc = netCDF4.Dataset(url)
    kh=nc['kh'][0,::10]
    plt.hist(kh)
    plt.show()
    #a=xr.open_dataset()
    #ds = xr.open_dataset(l['dap'][0],decode_times=False, engine='netcdf4')

    pass
