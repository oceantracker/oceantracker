#!/usr/bin/env python

from setuptools import setuptools, find_packages

setuptools.setup(name='oceantracker',
      python_requires='>=3.8',
      version='0.25',
      description='Particle tracker in the Ocean',
      author='Ross Vennell',
      author_email='ross.vennell@cawthron.org.nz ',
      url='https://www.cawthron.org.nz/',
      packages=find_packages(),
      install_requires=[],
)
