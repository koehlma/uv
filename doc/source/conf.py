#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (C) 2016, Maximilian Köhl <mail@koehlma.de>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/>.

import os
import re
import sys

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

callable_type = re.compile(r':type\s*(?P<name>[a-z_]+)?:\s*'
                           r'(\(+([a-zA-Z_.]+,\s*)*([a-zA-Z_.]+)\)'
                           r'\s*->\s*[a-zA-Z_.]+\s*\)*\s*\|?\s*)+')

argument_types = re.compile(r'\((([a-zA-Z_.]+,\s*)*([a-zA-Z_.]+))\)')
return_type = re.compile(r'->\s*([a-zA-Z_.]+)')


def convert_callable_types(app, what, name, obj, options, lines):
    docstring = '\n'.join(lines)
    match = callable_type.search(docstring)
    while match:
        if match.group('name'):
            replacement = ':type %s: Callable[[' % match.group('name')
        else:
            replacement = ':type: Callable[['
        replacement += argument_types.search(match.group(0)).group(1)
        replacement += '], ' + return_type.search(match.group(0)).group(1)
        replacement += ']'
        docstring = docstring[:match.start()] + replacement + docstring[match.end():]
        match = callable_type.search(docstring)
    lines[:] = docstring.splitlines()


def setup(app):
    app.connect('autodoc-process-docstring', convert_callable_types)
