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
import os.path
import platform
import re
import shutil
import subprocess
import sys

from distutils import log
from distutils.command.sdist import sdist
from distutils.command.build_ext import build_ext
from distutils.command.bdist_wininst import bdist_wininst
from distutils.errors import DistutilsError

try:
    from distutils.command.bdist_msi import bdist_msi
except ImportError:
    bdist_msi = None

from setuptools import setup

import cffi

__dir__ = os.path.dirname(__file__)


DEPS_PATH = 'deps'

LIBUV_PATH = os.path.join(DEPS_PATH, 'libuv')
LIBUV_REPO = 'https://github.com/libuv/libuv.git'
LIBUV_BRANCH = 'v1.x'
LIBUV_TAG = 'v1.8.0'

GYP_PATH = os.path.join(LIBUV_PATH, 'build', 'gyp')
GYP_REPO = 'https://chromium.googlesource.com/external/gyp.git'

WIN32_LIBRARIES = ['libuv', 'advapi32', 'iphlpapi', 'psapi',
                   'shell32', 'userenv', 'ws2_32']

_path_1 = os.path.expandvars(r'%SYSTEMDRIVE%\Program Files (x86)\Python 2.7\python.exe')
_path_2 = os.path.expandvars(r'%SYSTEMDRIVE%\Python27\python.exe')
WIN32_PYTHON27_PATHS = [_path_1, _path_2]


LICENSE = 'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)'


with open(os.path.join(__dir__, 'uv', 'metadata.py'), 'rb') as metadata_py:
    metadata_source = metadata_py.read().decode('utf-8')

match = re.search(r'__version__ = \'(.+?)\'', metadata_source)
version = match.group(1)

with open(os.path.join(__dir__, 'README.rst'), 'rb') as readme_file:
    long_description = readme_file.read().decode('utf-8')

with open(os.path.join(__dir__, 'cffi_source.c'), 'rb') as cffi_source:
    source = cffi_source.read().decode('utf-8').replace('__version__', version)

with open(os.path.join(__dir__, 'cffi_declarations.c'), 'rb') as cffi_declarations:
    declarations = cffi_declarations.read().decode('utf-8')

with open(os.path.join(__dir__, 'cffi_template.py'), 'rb') as cffi_template:
    uvcffi_code = cffi_template.read().decode('utf-8').format(**locals())

with open(os.path.join(__dir__, 'uvcffi', '__init__.py'), 'wb') as uvcffi_module:
    uvcffi_module.write(uvcffi_code.encode('utf-8'))


ffi = cffi.FFI()
ffi.cdef(declarations)

try:
    ffi.set_source('_uvcffi', source)
    extension = ffi.distutils_extension()
except AttributeError:
    from cffi.verifier import Verifier
    verifier = Verifier(ffi, source, modulename='_uvcffi')
    extension = verifier.get_extension()


def choose_path(paths):
    for path in paths:
        if os.path.exists(path):
            return path


def win32_find_python27():
    assert sys.platform == 'win32'
    python27 = None
    if sys.version_info[:2] == (2, 7):
        return sys.executable
    if 'PYTHON' in os.environ and os.environ['PYTHON'].endswith('.exe'):
        python27 = os.environ['PYTHON']
    if python27 is None or not os.path.isfile(python27):
        python27 = choose_path(WIN32_PYTHON27_PATHS)
    if not python27 or not os.path.isfile(python27):
        raise RuntimeError('python 2.7 interpreter not found')
    cmd = [python27, '--version']
    stderr = subprocess.STDOUT
    py_version = subprocess.check_output(cmd, stderr=stderr)[7:].decode().strip()
    if not py_version.startswith('2.7'):
        raise RuntimeError('invalid version of python interpreter (%s)' % py_version)
    return python27


def build_environ():
    environ = dict(os.environ)

    if sys.platform == 'win32':
        if os.environ.get('SET_SDK', None) == 'Y':
            environ.pop('VS140COMNTOOLS', None)
            environ.pop('VS120COMNTOOLS', None)
            environ.pop('VS110COMNTOOLS', None)
            if sys.version_info < (3, 3):
                environ.pop('VS100COMNTOOLS', None)
                environ['GYP_MSVS_VERSION'] = '2008'
            else:
                environ['GYP_MSVS_VERSION'] = '2010'
        environ['PYTHON'] = win32_find_python27()
    else:
        if 'CFLAGS' not in environ: environ['CFLAGS'] = ''
        environ['CFLAGS'] += ' -fPIC'

    return environ


def clone_libuv():
    log.info('cloning libuv...')
    cmd = ['git', 'clone', '-b', LIBUV_BRANCH, LIBUV_REPO, LIBUV_PATH]
    subprocess.check_call(cmd)
    subprocess.check_call(['git', 'checkout', LIBUV_TAG], cwd=LIBUV_PATH)


def clone_gyp():
    log.info('cloning gyp...')
    subprocess.call(['git', 'clone', GYP_REPO, GYP_PATH])


def build_libuv():
    log.info('building libuv...')
    env = build_environ()
    if sys.platform == 'win32':
        architecture = {'32bit': 'x86', '64bit': 'x64'}[platform.architecture()[0]]
        cmd = ['vcbuild.bat', architecture, 'release']
        subprocess.check_call(cmd, shell=True, cwd=LIBUV_PATH, env=env)
    else:
        subprocess.check_call(['sh', 'autogen.sh'], cwd=LIBUV_PATH, env=env)
        subprocess.check_call(['./configure'], cwd=LIBUV_PATH, env=env)
        subprocess.check_call(['make'], cwd=LIBUV_PATH, env=env)


def clean_libuv():
    log.info('cleaning libuv...')
    if sys.platform == 'win32':
        cmd = ['vcbuild.bat', 'clean']
        env = build_environ()
        subprocess.check_call(cmd, shell=True, cwd=LIBUV_PATH, env=env)
    else:
        subprocess.check_call(['make', 'clean'], cwd=LIBUV_PATH)
        subprocess.check_call(['make', 'distclean'], cwd=LIBUV_PATH)


def clean_build():
    log.info('cleaning build...')
    shutil.rmtree(DEPS_PATH)


class BuildExtensions(build_ext):
    user_options = build_ext.user_options[:]
    user_options.extend([
        ('libuv-build-clean', None, 'Clean libuv tree before compilation.'),
        ('libuv-force-fetch', None, 'Remove libuv (if present) and fetch it again.'),
        ('use-system-libuv', None, 'Use the system provided version of libuv.')
    ])

    boolean_options = build_ext.boolean_options[:]
    boolean_options.extend(['libuv-build-clean', 'libuv-force-fetch', 'use-system-libuv'])

    def __init__(self, dist):
        build_ext.__init__(self, dist)
        self.libuv_build_clean = False
        self.libuv_force_fetch = False
        self.use_system_libuv = False

    def initialize_options(self):
        self.libuv_build_clean = False
        self.libuv_force_fetch = False
        self.use_system_libuv = False
        build_ext.initialize_options(self)

    def build_extensions(self):
        if not os.path.exists(DEPS_PATH): os.mkdir(DEPS_PATH)

        if sys.platform.startswith('linux'):
            extension.libraries.append('rt')
        elif sys.platform == 'win32':
            self.compiler.add_library_dir(os.path.join(LIBUV_PATH, 'Release', 'lib'))
            extension.libraries.extend(WIN32_LIBRARIES)
            extension.define_macros.append(('WIN32', 1))
            extension.extra_link_args.extend(['/NODEFAULTLIB:libcmt', '/LTCG'])
        elif sys.platform.startswith('freebsd'):
            extension.libraries.append('kvm')

        if self.use_system_libuv:
            if sys.platform == 'win32':
                msg = 'using a system provided libuv is not supported on Windows'
                raise DistutilsError(msg)
            extension.libraries.append('uv')
        else:
            self.use_bundled_libuv()

        build_ext.build_extensions(self)

    def use_bundled_libuv(self):
        if self.libuv_force_fetch:
            shutil.rmtree(LIBUV_PATH)

        if not os.path.exists(LIBUV_PATH):
            try:
                clone_libuv()
            except Exception:
                shutil.rmtree(LIBUV_PATH)
                raise

        if self.libuv_build_clean:
            clean_libuv()

        build_libuv()

        self.compiler.add_include_dir(os.path.join(LIBUV_PATH, 'include'))
        if sys.platform != 'win32':
            libuv_lib = os.path.join(LIBUV_PATH, '.libs', 'libuv.a')
            extension.extra_objects.append(libuv_lib)


class SourceDistribution(sdist):
    def initialize_options(self):
        sdist.initialize_options(self)
        if not os.path.exists(DEPS_PATH): os.mkdir(DEPS_PATH)
        clean_build()
        clone_libuv()
        clone_gyp()
        shutil.rmtree(os.path.join(LIBUV_PATH, '.git'))
        shutil.rmtree(os.path.join(GYP_PATH, '.git'))
        shutil.rmtree(os.path.join(GYP_PATH, 'test'))


if os.environ.get('READTHEDOCS', None) == 'True':
    cmdclass = {}
    ext_modules = []
else:
    cmdclass = {'build_ext': BuildExtensions, 'sdist': SourceDistribution}
    ext_modules = [extension]


class WindowsInstaller(bdist_wininst):
    def get_inidata(self):
        self.distribution.metadata.author = 'Maximilian Koehl'
        return bdist_wininst.get_inidata(self)


cmdclass['bdist_wininst'] = WindowsInstaller


if bdist_msi is not None:
    msi_clean_regex = r'[0-9]+\.[0-9]+\.[0-9]+'

    class WindowsMSI(bdist_msi):
        def run(self):
            import re
            cleaned = re.search(msi_clean_regex, self.distribution.metadata.version)
            self.distribution.metadata.version = cleaned.group(0)
            bdist_msi.run(self)

    cmdclass['bdist_msi'] = WindowsMSI


setup(name='uv',
      version=version,
      description='Python libuv CFFI Bindings',
      long_description=long_description,
      author='Maximilian Köhl',
      author_email='mail@koehlma.de',
      url='https://github.com/koehlma/uv',
      packages=['uv', 'uvcffi'],
      cmdclass=cmdclass,
      ext_modules=ext_modules,
      requires=['cffi'],
      classifiers=[
          'Development Status :: 2 - Pre-Alpha',
          'Intended Audience :: Developers',
          LICENSE,
          'Operating System :: POSIX :: Linux',
          'Operating System :: POSIX :: BSD :: FreeBSD',
          'Operating System :: Microsoft :: Windows',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.2',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: Implementation :: CPython',
          'Programming Language :: Python :: Implementation :: PyPy',
          'Topic :: Internet'
      ])
