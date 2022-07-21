import yaml

def write_YAML(file_name,d):
    with open(file_name, 'w') as file:
        documents = yaml.safe_dump(d, file)

def read_YAML(file_name):
    with open(file_name, "r") as stream:
        try:
            params =yaml.safe_load(stream)
        except yaml.YAMLError as e:
            print('basic_util.py Error loading yaml file- ' + file_name)
            raise(e)

    return params
