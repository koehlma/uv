Python LibUV CFFI Bindings
==========================
This package aims to provide an object oriented wrapper around the LibUV
asynchronous IO library.

Features
--------
- full featured event loop backed by epoll, kqueue, IOCP and events ports
- asynchronous TCP and UDP sockets
- asynchronous SSL sockets (based on Python's SSL module)
- asynchronous DNS resolution
- asynchronous file and file system operations
- asynchronous file system events
- cross platform ANSI escape code controlled TTY
- IPC with socket sharing, using UNIX domain sockets or named pipes (Windows)
- child processes
- signal handling
- PyPy and CPython support (but only Python Language version 3)

Status
------
.. image:: https://travis-ci.org/koehlma/uv.svg?branch=master
    :target: https://travis-ci.org/koehlma/uv

.. image:: https://ci.appveyor.com/api/projects/status/jpa8jt5o9m7ow8ep/branch/master?svg=true
    :target: https://ci.appveyor.com/project/koehlma/uv

.. image:: https://readthedocs.org/projects/uv/badge/?version=latest
    :target: http://uv.readthedocs.org/en/latest/?badge=latest