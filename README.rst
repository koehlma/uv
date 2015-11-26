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


-----

|pypi| |unix_build| |windows_build|

-----

.. |pypi| image:: https://img.shields.io/pypi/v/uv.svg?style=flat-square&label=latest%20version
    :target: https://pypi.python.org/pypi/uv

.. |unix_build| image:: https://img.shields.io/travis/koehlma/uv/master.svg?style=flat-square&label=unix%20build
    :target: https://travis-ci.org/koehlma/uv

.. |windows_build| image:: https://img.shields.io/appveyor/ci/koehlma/uv.svg?style=flat-square&label=windows%20build
    :target: https://ci.appveyor.com/project/koehlma/uv

.. |docs| image:: https://readthedocs.org/projects/uv/badge/?version=latest&style=flat-square
    :target: https://uv.readthedocs.org/en/latest/