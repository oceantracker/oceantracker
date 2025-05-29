#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='oceantracker',
      python_requires='>=3.10',
      version='0.5.1.3',
      description='Fast offline Lagrangian particle tracking in the Ocean',
      long_description=open('README.md').read(),
      long_description_content_type='text/markdown',
      author='Ross Vennell & Laurin Steidle',
      author_email='ross.vennell@cawthron.org.nz',
      url='https://oceantracker.github.io/oceantracker/',
      license='MIT',
      packages=find_packages(),
      install_requires=[
          'numpy',
          'numba',
          'netcdf4',
          'xarray',
          'scipy',
          'pyproj',
          'setuptools',
          'psutil',
          'matplotlib',
          'pyyaml',
      ],
      classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: Science/Research',
          'Operating System :: OS Independent',
          'Topic :: Scientific/Engineering :: Oceanography',
          ],
)
