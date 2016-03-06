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

from __future__ import print_function, unicode_literals, division, absolute_import

from collections import namedtuple

from . import common, error, handle, library, request
from .library import ffi, lib

Timespec = namedtuple('Timespec', ['sec', 'nsec'])

Stat = namedtuple('Stat', ['dev', 'mode', 'nlink', 'uid', 'gid', 'rdev',
                           'ino', 'size', 'blksize', 'blocks', 'flags', 'gen',
                           'atim', 'mtim', 'ctim', 'birthtim'])

Dirent = namedtuple('Dirent', ['name', 'type'])

requests = set()


def unpack_timespec(uv_timespec):
    return Timespec(uv_timespec.tv_sec, uv_timespec.tv_nsec)


def unpack_stat(uv_stat):
    return Stat(uv_stat.st_dev, uv_stat.st_mode, uv_stat.st_nlink, uv_stat.st_uid,
                uv_stat.st_gid, uv_stat.st_rdev, uv_stat.st_ino, uv_stat.st_size,
                uv_stat.st_blksize, uv_stat.st_blocks, uv_stat.st_flags, uv_stat.st_gen,
                unpack_timespec(uv_stat.st_atim), unpack_timespec(uv_stat.st_mtim),
                unpack_timespec(uv_stat.st_ctim), unpack_timespec(uv_stat.st_birthtim))


def unpack_dirent(uv_dirent):
    return Dirent(ffi.string(uv_dirent.name).decode(), DirentType(uv_dirent.type))


class FSType(common.Enumeration):
    UNKNOWN = lib.UV_FS_UNKNOWN
    CUSTOM = lib.UV_FS_CUSTOM
    OPEN = lib.UV_FS_OPEN
    CLOSE = lib.UV_FS_CLOSE
    READ = lib.UV_FS_READ
    WRITE = lib.UV_FS_WRITE
    SENDFILE = lib.UV_FS_SENDFILE
    STAT = lib.UV_FS_STAT
    LSTAT = lib.UV_FS_LSTAT
    FSTAT = lib.UV_FS_FSTAT
    FTRUNCATE = lib.UV_FS_FTRUNCATE
    UTIME = lib.UV_FS_UTIME
    FUTIME = lib.UV_FS_FUTIME
    ACCESS = lib.UV_FS_ACCESS
    CHMOD = lib.UV_FS_CHMOD
    FCHMOD = lib.UV_FS_FCHMOD
    FSYNC = lib.UV_FS_FSYNC
    FDATASYNC = lib.UV_FS_FDATASYNC
    UNLINK = lib.UV_FS_UNLINK
    RMDIR = lib.UV_FS_RMDIR
    MKDIR = lib.UV_FS_MKDIR
    MKDTEMP = lib.UV_FS_MKDTEMP
    RENAME = lib.UV_FS_RENAME
    SCANDIR = lib.UV_FS_SCANDIR
    LINK = lib.UV_FS_LINK
    SYMLINK = lib.UV_FS_SYMLINK
    READLINK = lib.UV_FS_READLINK
    CHOWN = lib.UV_FS_CHOWN
    FCHOWN = lib.UV_FS_FCHOWN

    def __call__(self, postprocessor):
        self.postprocessor = postprocessor
        return postprocessor


class DirentType(common.Enumeration):
    UNKNOWN = lib.UV_DIRENT_UNKNOWN
    FILE = lib.UV_DIRENT_FILE
    DIR = lib.UV_DIRENT_DIR
    LINK = lib.UV_DIRENT_LINK
    FIFO = lib.UV_DIRENT_FIFO
    SOCKET = lib.UV_DIRENT_SOCKET
    CHAR = lib.UV_DIRENT_CHAR
    BLOCK = lib.UV_DIRENT_BLOCK


@request.RequestType.FS
class FSRequest(request.UVRequest):
    __slots__ = ['uv_fs', 'data', 'callback']

    def __init__(self, data=None, callback=None, loop=None):
        self.uv_fs = ffi.new('uv_fs_t*')
        super(FSRequest, self).__init__(self.uv_fs, loop)
        self.data = data
        self.callback = callback or common.dummy_callback
        requests.add(self)

    @property
    def result(self):
        return self.uv_fs.result

    @property
    def ptr(self):
        return self.uv_fs.ptr

    @property
    def path(self):
        return ffi.string(self.uv_fs.path).decode()

    @property
    def fs_type(self):
        return FSType(self.uv_fs.fs_type)

    @property
    def stat(self):
        return unpack_stat(self.uv_fs.statbuf)


@FSType.CLOSE
def post_close(request):
    status = error.StatusCodes.get(request.result)
    return [status]





@FSType.STAT
def post_stat(request):
    status = error.StatusCodes.get(request.result)
    return [status, request.stat]


@ffi.callback('uv_fs_cb')
def fs_callback(uv_request):
    fs_request = library.detach(uv_request)
    """ :type: uv.FSRequest """
    try:
        fs_request.callback(fs_request, *fs_request.fs_type.postprocessor(fs_request))
    except:
        fs_request.loop.handle_exception()
    lib.uv_fs_req_cleanup(uv_request)
    fs_request.set_closed()


def close(fd, callback=None, loop=None):
    request = FSRequest(None, callback, loop)
    code = lib.cross_uv_fs_close(request.loop.uv_loop, request.uv_fs, fd, fs_callback)
    if code != error.StatusCodes.SUCCESS:
        raise error.UVError(code)
    return request


@FSType.OPEN
def post_open(request):
    if request.result < 0: status, fd = error.StatusCodes.get(request.result), None
    else: status, fd = error.StatusCodes.SUCCESS, request.result
    return [status, fd]


def open(path, flags, mode=0o777, callback=None, loop=None):
    """

    :param path:
    :param flags:
    :param mode:
    :param callback: callback signature: `(request, status, fd)`
    :param loop:

    :type path: str
    :type flags: int
    :type mode: int
    :type callback: (FSRequest, int, int) -> None

    :return:
    """
    fs_request = FSRequest(None, callback, loop)
    uv_fs = request.uv_fs
    c_path = path.encode()
    code = lib.uv_fs_open(fs_request.loop.uv_loop, uv_fs, c_path, flags, mode,
                          fs_callback)
    if code != error.StatusCodes.SUCCESS:
        raise error.UVError(code)
    return request


def stat(path, callback=None, loop=None):
    fs_request = FSRequest(callback=callback, loop=loop)
    code = lib.uv_fs_stat(fs_request.loop.uv_loop, fs_request.uv_fs, path.encode(),
                          fs_callback)
    if code != error.StatusCodes.SUCCESS:
        raise error.UVError(code)
    return request


@handle.HandleTypes.FILE
class File(object):
    pass
