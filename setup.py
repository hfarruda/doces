#!/usr/bin/env python3
"""
MIT License

Copyright (c) 2024 Henrique Ferraz de Arruda, Kleber A. Oliveira, and Yamir Moreno

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
import os.path
import platform
import sys

print("Building on:", sys.version)

with open("requirements.txt", "r", encoding="utf8") as fh:
    requirements = fh.readlines()

enable_parallelism = False #False, because this version of DOCES is not implemented in parallel.

extra_options = []
extra_link_options = []
extra_includes_paths = []
extra_library_paths = []
compiler_options = [
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
            ]

if(platform.system()=="Darwin"):
    extra_options = ["-D OSX"]
    if(enable_parallelism):
        extra_options += ["-DCV_USE_LIBDISPATCH=1"]
elif(platform.system()=="Windows"):
    extra_options += ["/D WIN32"]
    extra_options += ["/D __WIN32__"]
    compiler_options = [
                "/std:c11",
                "/Wall",
                "/O2",
            ]
    if(enable_parallelism):
        extra_options+=["/D CV_USE_OPENMP=1"]
        extra_options+=["/openmp"]
    
    if("VCPKG_INSTALLATION_ROOT" in os.environ):
        extra_includes_paths += [os.path.join(os.environ["VCPKG_INSTALLATION_ROOT"], "installed", "x64-windows-static","include")]
        extra_library_paths += [os.path.join(os.environ["VCPKG_INSTALLATION_ROOT"], "installed", "x64-windows-static","lib")]

elif(platform.system()=="Linux"):
    extra_options = ["-D Linux","-D_GNU_SOURCE=1"]
    if(enable_parallelism):
        extra_options += ["-DCV_USE_OPENMP=1","-fopenmp"]
        extra_link_options+=["-lgomp"]
else:
    if(enable_parallelism):
        extra_options += ["-DCV_USE_OPENMP=1","-fopenmp"]
        extra_link_options+=["-lgomp"]

# WORKAROUND: https://stackoverflow.com/questions/54117786/add-numpy-get-include-argument-to-setuptools-without-preinstalled-numpy
class get_numpy_include(object):
    def __str__(self):
            import numpy
            return numpy.get_include()

with open("README.md", "r") as fh:
    long_description = fh.read()

building_on_windows = platform.system() == "Windows"

package_name = "doces"

with open(os.path.join(package_name,"Python", "version.h"),"rt") as fd:
    version = fd.readline().strip().split(" ")[-1]

print("Compiling version %s"%version)
setup(
    name=package_name,
    version=version,
    author="Henrique F. de Arruda, Kleber A. Oliveira, and Yamir Moreno",
    author_email="h.f.arruda@gmail.com",
    install_requires=[req for req in requirements if req[:2] != "# "],
    setup_requires=['wheel',"numpy"],
    description="DOCES is an experimental library to simulate opinion dynamics on complex networks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hfarruda/doces",
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
            ]+extra_includes_paths,
            extra_compile_args=compiler_options+extra_options,
            extra_link_args=extra_link_options,
            library_dirs=extra_library_paths,
            libraries = ["getopt"] if building_on_windows else [],
        ),
    ]
)
