#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

import os

__dir__ = os.path.dirname(__file__)

sys.path.insert(0, os.path.join(__dir__, '..', '..'))

os.environ['PYTHON_MOCK_LIBUV'] = 'True'

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

project = 'Python libuv CFFI Bindings'
copyright = '2015, Maximilian Köhl'
author = 'Maximilian Köhl'

version = uv.__version__
release = uv.__version__

language = None

exclude_patterns = []

pygments_style = 'sphinx'

todo_include_todos = False

html_static_path = ['_static']

intersphinx_mapping = {'python': ('https://docs.python.org/3.5', None)}
