# ----------- get version number ------------------------------------------------

from importlib.metadata import version

__version__ = version("oceantracker")


# ----------- get version publishing date ---------------------------------------

import requests
from datetime import datetime

def get_package_release_date(package_name, version=None):
    """Get the release date of a package from PyPI."""
    url = f"https://pypi.org/pypi/{package_name}/json"
    
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        
        if version is None:
            # Get the latest version
            version = data['info']['version']
            # print(version)
        
        if version in data['releases']:
            release_info = data['releases'][version]
            if release_info:  # Check if release info exists
                upload_time = release_info[0]['upload_time_iso_8601']
                return datetime.fromisoformat(upload_time.replace('Z', '+00:00'))
        
        return None
    else:
        raise Exception(f"Failed to fetch data for {package_name}")

try:
    release_date = get_package_release_date("oceantracker",__version__)
    __release_date__ = str(release_date)[:19]
except:
    __release_date__ = 'unknown'