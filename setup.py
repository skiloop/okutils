#!/bin/env python
# -*- coding:utf8 -*-
import sys

from setuptools import find_packages, setup, Extension

include_dirs, library_dirs = [], []
if sys.platform == 'darwin':
    include_dirs.append("/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/usr/include")
    library_dirs.append("/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/usr/lib")

tools_ext = Extension(
    'okutils.tools',
    sources=['lib/funcs.cpp', 'lib/utils.cpp'],
    include_dirs=include_dirs, library_dirs=library_dirs,
    extra_compile_args=['-std=c++11'],
)

setup(
    packages=find_packages(exclude=('tests', 'tests.*')),
    ext_modules=[tools_ext]
)
