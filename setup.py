#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2019 Bitergia
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# Authors:
#     Santiago Dueñas <sduenas@bitergia.com>
#     Jesus M. Gonzalez-Barahona <jgb@gsyc.es>
#

import codecs
import os.path
import re

from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))
readme_md = os.path.join(here, 'README.md')
version_py = os.path.join(here, 'sirmordred', '_version.py')

# Get the package description from the README.md file
with codecs.open(readme_md, encoding='utf-8') as f:
    long_description = f.read()

with codecs.open(version_py, 'r', encoding='utf-8') as fd:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        fd.read(), re.MULTILINE).group(1)


setup(name="sirmordred",
      description="Drive GrimoireLab tools to produce a dashboard",
      long_description=long_description,
      long_description_content_type='text/markdown',
      url="https://github.com/chaoss/grimoirelab-sirmordred",
      version=version,
      author="CHAOSS",
      author_email="acs@bitergia.com",
      license="GPLv3",
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Intended Audience :: Developers',
          'Topic :: Software Development',
          'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
          'Programming Language :: Python :: 3'
      ],
      keywords="development repositories analytics git github bugzilla jira jenkins",
      packages=[
          'sirmordred'
      ],
      install_requires=[
          'grimoire-elk>=0.32',
          'kidash>=0.4.13',
          'grimoirelab-panels>=0.0.7',
          'sortinghat>=0.7',
          'elasticsearch==6.3.1',
          'elasticsearch-dsl==6.3.1',
          'file-read-backwards==2.0.0',
          'colorlog==4.1.0'
      ],
      scripts=[
          'bin/sirmordred',
          'utils/healthcheck.py',
          'utils/micro.py',
          'utils/panels_config.py'
      ],
      zip_safe=False)
