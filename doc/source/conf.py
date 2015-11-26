#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

import os

__dir__ = os.path.dirname(__file__)

sys.path.insert(0, os.path.join(__dir__, '..', '..'))

import uv

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.mathjax',
    'sphinx.ext.viewcode',
]

templates_path = ['_templates']

source_suffix = '.rst'

master_doc = 'index'

project = 'Python LibUV'
copyright = '2015, Maximilian Köhl'
author = 'Maximilian Köhl'

version = uv.__version__
release = uv.__version__

language = None

exclude_patterns = []

pygments_style = 'sphinx'

todo_include_todos = True

import sphinx_rtd_theme

html_theme = "sphinx_rtd_theme"
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

html_static_path = ['_static']

intersphinx_mapping = {'https://docs.python.org/': None}
