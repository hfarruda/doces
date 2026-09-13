@echo off
setlocal
set "PROJECT_DIR=%~dp0.."
rem Run from a Visual Studio developer prompt with getopt configured as in CI.
set "PYTHON_VERSIONS=%*"
if "%PYTHON_VERSIONS%"=="" set "PYTHON_VERSIONS=3.9 3.10 3.11 3.12 3.13 3.14"
for %%V in (%PYTHON_VERSIONS%) do (
    call :build_version %%V
    if errorlevel 1 exit /b 1
)
exit /b 0

:build_version
set "BUILD_ENV=%TEMP%\doces-python-%~1-%RANDOM%-%RANDOM%"
call conda create --yes --prefix "%BUILD_ENV%" --override-channels -c conda-forge python=%~1 pip
if errorlevel 1 exit /b 1
call conda run --prefix "%BUILD_ENV%" --no-capture-output python "%PROJECT_DIR%\build-scripts\build_and_test.py" --output-dir "%PROJECT_DIR%\dist"
if errorlevel 1 exit /b 1
call conda env remove --yes --prefix "%BUILD_ENV%"
exit /b %ERRORLEVEL%
