Python »libuv« CFFI Wrapper
===========================

|pypi| |unix_build| |windows_build| |coverage| |docs|

This package aims to provide an object oriented CFFI based wrapper around the libuv
asynchronous IO library. It supports all handles of libuv as well as filesystem
operations, dns utility functions and miscellaneous utilities.

State
=====

:handles: stable API, well tested, completely documented
:dns: stable API, well tested, completely documented
:fs: planning
:misc: planning
:ssl: planning

Features
========
- full featured event loop backed by epoll, kqueue, IOCP and events ports
- asynchronous TCP and UDP sockets
- asynchronous SSL sockets (based on Python's SSL module)
- asynchronous DNS resolution
- asynchronous file and file system operations
- asynchronous file system events
- cross platform ANSI escape code controlled TTY
- IPC with socket sharing, using UNIX domain sockets or named pipes (Windows)
- child processes and signal handling
- cross platform memory, CPU and network interface information
- timer and high resolution clock
- supported Python interpreters and versions:

  - **CPython**: 2.7, 3.3, 3.4, 3.5
  - **PyPy**: 4.0 (Windows and Linux)
  - **PyPy3**: 2.4.0, 2.7.0-alpha0 (Linux Only)

- PyCharm type hinting support
- PEP 3151 compatible exceptions


.. |pypi| image:: https://img.shields.io/pypi/v/uv.svg?style=flat-square&label=latest%20version
    :target: https://pypi.python.org/pypi/uv

.. |unix_build| image:: https://img.shields.io/travis/koehlma/uv/master.svg?style=flat-square&label=unix%20build
    :target: https://travis-ci.org/koehlma/uv

.. |windows_build| image:: https://img.shields.io/appveyor/ci/koehlma/uv.svg?style=flat-square&label=windows%20build
    :target: https://ci.appveyor.com/project/koehlma/uv

.. |docs| image:: https://readthedocs.org/projects/uv/badge/?version=master&style=flat-square
    :target: https://uv.readthedocs.org/en/master/

.. |coverage| image:: https://img.shields.io/coveralls/koehlma/uv/master.svg?style=flat-square
    :target: https://coveralls.io/github/koehlma/uv?branch=master
