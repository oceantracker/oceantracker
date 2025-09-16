"""
Configuration file for the Sphinx documentation builder.

This file only contains a selection of the most common options. For a full
list see the documentation:
https://www.sphinx-doc.org/en/master/usage/configuration.html
"""

# -- Path setup --------------------------------------------------------------

import os
import sys
from pathlib import Path
from datetime import datetime

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath('..'))

# -- Project information -----------------------------------------------------

project = 'OceanTracker'
copyright = f'{datetime.now().year}, R. Vennell'
author = 'R. Vennell & L. Steidle'

# The full version, including alpha/beta/rc tags
# Try to get version from package
try:
    import oceantracker
    release = oceantracker.__version__
except ImportError:
    release = 'Beta 0.5'

version = release

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'sphinx.ext.githubpages',
    'sphinx_autodoc_typehints',
    'sphinx_toolbox.collapse',
    'sphinx_changelog',
    'myst_parser',
    'nbsphinx',
    'autodocsumm',
    'rst2pdf.pdfbuilder',
]

# Support for both .rst and .md files
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', '**.ipynb_checkpoints']

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.
html_theme = 'alabaster'


# Add any paths that contain custom static files (such as style sheets)
html_static_path = ['_static']

# Custom sidebar templates
html_sidebars = {
    '**': [
        'about.html',
        'navigation.html',
        'relations.html',
        'searchbox.html',
    ]
}

# Theme options are theme-specific and customize the look and feel
html_theme_options = {
    'logo': 'ocean_tracker.png',
    'logo_name': release,
    'fixed_sidebar': True,
    'show_relbar_bottom': True,
    'github_user': 'oceantracker',
    'github_repo': 'oceantracker',
    'github_button': True
}