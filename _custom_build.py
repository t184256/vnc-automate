#!/usr/bin/python3
# SPDX-FileCopyrightText: 2016-2023 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from setuptools import Extension
from setuptools.command.build_py import build_py as _build_py


class build_py(_build_py):
    def run(self):
        self.run_command("build_ext")
        return super().run()

    def initialize_options(self):
        super().initialize_options()

        from Cython.Build import cythonize
        import numpy

        if self.distribution.ext_modules is None:
            self.distribution.ext_modules = []

        self.distribution.ext_modules.extend(cythonize([
            Extension(
                "vncautomate.segment_line",
                sources=["src/vncautomate/segment_line.pyx"],
                language="c++",
                include_dirs=[numpy.get_include()],
            )
        ]))
