#!/bin/env python
# -*- coding:utf8 -*-
from distutils.core import setup, Extension

from setuptools import find_packages

tools_ext = Extension('okutils.tools', sources=['lib/funcs.cpp', 'lib/utils.win.cpp'])

setup(
    packages=find_packages(exclude=('tests', 'tests.*')),
    ext_modules=[tools_ext]
)
