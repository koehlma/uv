@ECHO OFF

SET COMMAND_TO_RUN=%*
SET WIN_SDK_ROOT=C:\Program Files\Microsoft SDKs\Windows

SET SET_SDK=Y
SET MAJOR_PYTHON_VERSION=%PYTHON_VERSION:~0,1%
IF "%PYTHON_VERSION:~3,1%" == "." (
    SET MINOR_PYTHON_VERSION=%PYTHON_VERSION:~2,1%
) ELSE (
    SET MINOR_PYTHON_VERSION=%PYTHON_VERSION:~2,2%
)

IF %MAJOR_PYTHON_VERSION% == 2 (
    SET WINDOWS_SDK_VERSION="v7.0"
) ELSE IF %MAJOR_PYTHON_VERSION% == 3 (
    SET WINDOWS_SDK_VERSION="v7.1"
    IF %MINOR_PYTHON_VERSION% GTR 4 (
        SET SET_SDK=N
    )
) ELSE (
    ECHO Unsupported Python version: "%MAJOR_PYTHON_VERSION%"
    EXIT 1
)

IF "%PYTHON_PYPY:~0,4%" == "pypy" (
    SET SET_SDK=Y
    SET WINDOWS_SDK_VERSION="v7.0"
)

IF %SET_SDK% == Y (
    IF "%PYTHON_ARCH%" == "64" (
        ECHO Configuring Windows SDK %WINDOWS_SDK_VERSION% for Python %MAJOR_PYTHON_VERSION% on a 64 bit architecture
        SET DISTUTILS_USE_SDK=1
        SET MSSdk=1
        "%WIN_SDK_ROOT%\%WINDOWS_SDK_VERSION%\Setup\WindowsSdkVer.exe" -q -version:%WINDOWS_SDK_VERSION%
        "%WIN_SDK_ROOT%\%WINDOWS_SDK_VERSION%\Bin\SetEnv.cmd" /x64 /release
        ECHO Executing: %COMMAND_TO_RUN%
        call %COMMAND_TO_RUN% || EXIT 1
    ) ELSE (
        ECHO Configuring Windows SDK %WINDOWS_SDK_VERSION% for Python %MAJOR_PYTHON_VERSION% on a 32 bit architecture
        SET DISTUTILS_USE_SDK=1
        SET MSSdk=1
        "%WIN_SDK_ROOT%\%WINDOWS_SDK_VERSION%\Setup\WindowsSdkVer.exe" -q -version:%WINDOWS_SDK_VERSION%
        "%WIN_SDK_ROOT%\%WINDOWS_SDK_VERSION%\Bin\SetEnv.cmd" /x86 /release
        ECHO Executing: %COMMAND_TO_RUN%
        call %COMMAND_TO_RUN% || EXIT 1
    )
) ELSE (
    ECHO Using default MSVC build environment for 32 bit architecture
    ECHO Executing: %COMMAND_TO_RUN%
    call %COMMAND_TO_RUN% || EXIT 1
)