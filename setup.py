#!/usr/bin/env python3
"""
MIT License

Copyright (c) 2023 Henrique Ferraz de Arruda, Kleber A. Oliveira

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

#This code is adapted from cxrandomwalk by Filipi Nascimento Silva.
#https://github.com/filipinascimento/cxrandomwalk

import setuptools
from setuptools import setup, Extension
import os.path;
import platform;

enable_parallelism = False #True

extraOptions = []
extraLinkOptions = []
extraIncludesPaths = []
extraLibraryPaths = []

if(platform.system()=="Darwin"):
    extraOptions = ["-D OSX"]
    if(enable_parallelism):
        extraOptions += ["-DCV_USE_LIBDISPATCH=1"]
elif(platform.system()=="Windows"):
    extraOptions += ["/D WIN32"]
    extraOptions += ["/D __WIN32__"]
    compilerOptions = [
                "/std:c11",
                "/Wall",
                "/O2",
            ]
    if(enable_parallelism):
        extraOptions+=["/D CV_USE_OPENMP=1"]
        extraOptions+=["/openmp"]
    
    if("VCPKG_INSTALLATION_ROOT" in os.environ):
        extraIncludesPaths += [os.path.join(os.environ["VCPKG_INSTALLATION_ROOT"], "installed", "x64-windows-static","include")]
        extraLibraryPaths += [os.path.join(os.environ["VCPKG_INSTALLATION_ROOT"], "installed", "x64-windows-static","lib")]

elif(platform.system()=="Linux"):
    extraOptions = ["-D Linux","-D_GNU_SOURCE=1"]
    if(enable_parallelism):
        extraOptions += ["-DCV_USE_OPENMP=1","-fopenmp"]
        extraLinkOptions+=["-lgomp"]
else:
    if(enable_parallelism):
        extraOptions += ["-DCV_USE_OPENMP=1","-fopenmp"]
        extraLinkOptions+=["-lgomp"]

# WORKAROUND: https://stackoverflow.com/questions/54117786/add-numpy-get-include-argument-to-setuptools-without-preinstalled-numpy
class get_numpy_include(object):
    def __str__(self):
            import numpy
            return numpy.get_include()

with open("README.md", "r") as fh:
    long_description = fh.read()

building_on_windows = platform.system() == "Windows"

package_name = "opiniondynamics"

with open(os.path.join(package_name,"Python", "version.h"),"rt") as fd:
    version = fd.readline().strip().split(" ")[-1]

print("Compiling version %s"%version)

setup(
    name=package_name,
    version=version,
    author="Henrique F. de Arruda and Kleber A. Oliveira",
    author_email="henrique.f.arruda@centai.eu, kleber.oliveira@centai.eu",
    setup_requires=['wheel',"numpy"],
    description="Experimental library to simulate opinion dynamics on complex networks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hfarruda/OpinionDynamics",
    packages=setuptools.find_packages(),
    classifiers=[
            "Programming Language :: Python :: 3",
            "License :: OSI Approved :: MIT License",
            "Operating System :: MacOS :: MacOS X",
            "Operating System :: Microsoft :: Windows",
            "Operating System :: POSIX :: Linux",
            "Development Status :: 3 - Alpha",
            "Programming Language :: C",
            "Topic :: Scientific/Engineering :: Opinion dyanamics",
            "Intended Audience :: Science/Research"
    ],
    python_requires='>=3.6',
    ext_modules = [
        Extension(
            package_name + "_core",
            sources=[
                os.path.join(package_name,"Source", "network.c"),
                os.path.join(package_name,"Source", "post.c"),
                os.path.join(package_name,"Source", "utils.c"),
                os.path.join(package_name,"Source", "dynamics.c"),
                os.path.join(package_name,"Python", "opinionDynamics.c"),
            ],
            include_dirs=[
                os.path.join(package_name,"Source"),
                os.path.join(package_name,"Python"),
                get_numpy_include()
            ]+extraIncludesPaths,
            extra_compile_args=[
                "-std=c11",
                "-Wall",
                "-Wno-unused-function",
                "-Wno-deprecated-declarations",
                "-Wno-sign-compare",
                "-Wno-strict-prototypes",
                "-Wno-unused-variable",
                "-O3",
                "-funroll-loops",
                "-fstrict-aliasing"
            ]+extraOptions,
            extra_link_args=extraLinkOptions,
            library_dirs=extraLibraryPaths,
            libraries = ["getopt"] if building_on_windows else [],
        ),
    ]
)
