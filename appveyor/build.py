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
import os.path
import subprocess

PYTHON = os.environ.get('PYTHON', None)
PYTHON_PYPY = os.environ.get('PYTHON_PYPY', None)

python_exe = os.path.join(PYTHON, 'python.exe')

__dir__ = os.path.dirname(__file__)

print(python_exe)

if PYTHON_PYPY:
    import shutil
    shutil.copy(os.path.join(__dir__, 'wheel_fix', 'bdist_wheel.py'),
                os.path.join(PYTHON, 'site-packages', 'wheel'))
    shutil.copy(os.path.join(__dir__, 'wheel_fix', 'metadata.py'),
                os.path.join(PYTHON, 'site-packages', 'wheel'))

subprocess.call(['%CMD_IN_ENV%', python_exe, 'setup.py', 'bdist_wheel'], shell=True)
subprocess.call(['%CMD_IN_ENV%', python_exe, 'setup.py', 'bdist_wininst'], shell=True)

if not PYTHON_PYPY:
    subprocess.call(['%CMD_IN_ENV%', python_exe, 'setup.py', 'bdist_msi'], shell=True)
