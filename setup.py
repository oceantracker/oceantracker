#!/usr/bin/env python

from setuptools import setup, find_packages

version= dict(major= 1.0,minor=0, revision  = 1, date = '2025-08-27')

setup(name='oceantracker',
      python_requires='>=3.10,<3.12',
      version=f"{version['major']:.2f}.{version['minor']:02d}.{version['revision']:04d}-{version['date']}",
      description='Fast offline Lagrangian particle tracking in the Ocean for structured and unstructured grids',
      author='',
      author_email='',
      url='https://oceantracker.github.io/oceantracker/',
      packages=find_packages(),
      install_requires=[],
)
