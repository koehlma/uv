# -*- coding: utf-8 -*-
#
# Copyright (C) 2015, Maximilian Köhl <mail@koehlma.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from collections import namedtuple
from .error import UVError
from .handle import HandleType
from .library import ffi, lib

Timeval = namedtuple('Timeval', ['sec', 'usec'])

ResourceUsage = namedtuple('ResourceUsage', ['utime', 'stime', 'maxrss', 'ixrss',
                                             'idrss', 'isrss', 'minflt', 'majflt',
                                             'nswap', 'inblock', 'oublock', 'msgsnd',
                                             'msgrcv', 'nsignals', 'nvcsw', 'nivcsw'])

CpuTimes = namedtuple('CpuTimes', ['user', 'nice', 'sys', 'idle', 'irq'])
CpuInfo = namedtuple('CpuInfo', ['model', 'speed', 'times'])

InterfaceAddress = namedtuple('InterfaceAddress', ['name', 'physical', 'internal',
                                                   'address', 'netmask'])


def unpack_timeval(uv_timeval):
    return Timeval(uv_timeval.tv_sec, uv_timeval.tv_usec)


def unpack_resource_usage(uv_resource_usage):
    pass


def unpack_cpu_times(uv_cpu_times):
    return CpuTimes(uv_cpu_times.user, uv_cpu_times.nice, uv_cpu_times.sys,
                    uv_cpu_times.idle, uv_cpu_times.irq)


def unpack_cpu_info(uv_cpu_info):
    model = ffi.string(uv_cpu_info.model).decode()
    return CpuInfo(model, uv_cpu_info.speed, unpack_cpu_times(uv_cpu_info.cpu_times))


def guess_handle(fd: int):
    uv_handle = lib.cross_uv_guess_handle(fd)
    return HandleType(uv_handle).cls


def kill(pid: int, signum: int):
    code = lib.uv_kill(pid, signum)
    if code < 0: raise UVError(code)

def cpu_info():
    uv_cpu_info_array = ffi.new('uv_cpu_info_t**')
    uv_cpu_info_count = ffi.new('int*')
    code = lib.uv_cpu_info(uv_cpu_info_array, uv_cpu_info_count)
    if code < 0: raise UVError(code)
    result = []
    try:
        for index in range(uv_cpu_info_count[0]):
            result.append(unpack_cpu_info(uv_cpu_info_array[0][index]))
    finally:
        lib.uv_free_cpu_info(uv_cpu_info_array[0], uv_cpu_info_count[0])
    return result


def hrtime():
    return lib.uv_hrtime()
