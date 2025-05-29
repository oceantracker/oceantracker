#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='oceantracker',
      python_requires='>=3.10',
      version='0.5.1.4',
      description='Fast offline Lagrangian particle tracking in the Ocean',
      long_description=open('README.md').read(),
      long_description_content_type='text/markdown',
      author='Ross Vennell & Laurin Steidle',
      author_email='ross.vennell@cawthron.org.nz',
      url='https://oceantracker.github.io/oceantracker/',
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
          'Programming Language :: Python :: 3.10',
          'Programming Language :: Python :: 3.11',
          'Programming Language :: Python :: 3.12',
          'Development Status :: 4 - Beta',
          'Intended Audience :: Science/Research',
          'License :: OSI Approved :: MIT License',
          'Operating System :: OS Independent',
          'Topic :: Scientific/Engineering :: Oceanography',
          ],
)
