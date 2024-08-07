#!/bin/env python
# -*- coding:utf8 -*-

from setuptools import find_packages, setup, Extension

tools_ext = Extension(
    'okutils.tools',
    sources=['lib/funcs.cpp', 'lib/utils.cpp'],
    extra_compile_args=['-std=c++11'],
)

setup(
    packages=find_packages(exclude=('tests', 'tests.*')),
    ext_modules=[tools_ext]
)
