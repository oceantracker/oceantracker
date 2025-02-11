import yaml
import numpy as np

def represent_datetime64(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:str', str(data))

yaml.SafeDumper.add_representer(np.datetime64, represent_datetime64)

def write_YAML(file_name,d):
    if '.yaml' in file_name.lower():
        fn = file_name
    else:
        fn = file_name + '.yaml'

    with open(fn, 'w') as file:
        documents = yaml.safe_dump(d, file)

def read_YAML(file_name):

    with open(file_name, "r") as stream:
        try:
            params =yaml.safe_load(stream)
        except yaml.YAMLError as e:
            print('basic_util.py Error loading yaml file- ' + file_name)
            raise(e)

    return params
