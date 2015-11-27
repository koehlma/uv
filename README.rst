Python libuv CFFI Bindings
==========================
|pypi| |unix_build| |windows_build| |docs| |implementations|

This package aims to provide an object oriented CFFI based wrapper around the libuv
asynchronous IO library. It supports all handles of libuv as well as filesystem
operations, dns utility functions and miscellaneous utilities.

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
- PyPy and CPython support (but only Python language version 3)


.. |pypi| image:: https://img.shields.io/pypi/v/uv.svg?style=flat-square&label=latest%20version
    :target: https://pypi.python.org/pypi/uv

.. |unix_build| image:: https://img.shields.io/travis/koehlma/uv/master.svg?style=flat-square&label=unix%20build
    :target: https://travis-ci.org/koehlma/uv

.. |windows_build| image:: https://img.shields.io/appveyor/ci/koehlma/uv.svg?style=flat-square&label=windows%20build
    :target: https://ci.appveyor.com/project/koehlma/uv

.. |docs| image:: https://readthedocs.org/projects/uv/badge/?version=latest&style=flat-square
    :target: https://uv.readthedocs.org/en/latest/

.. |implementations| image:: https://img.shields.io/pypi/implementation/uv.svg?style=flat-square
    :target: https://pypi.python.org/pypi/uv
