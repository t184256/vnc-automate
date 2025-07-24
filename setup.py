#!/usr/bin/python3
# SPDX-FileCopyrightText: 2016-2023 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from setuptools import Extension, setup
from Cython.Build import cythonize
import numpy


setup(
    ext_modules=cythonize([
        Extension(
            "vncautomate.segment_line",
            sources=["src/vncautomate/segment_line.pyx"],
            language="c++",
            include_dirs=[numpy.get_include()],
        ),
    ]),
)
