#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2017 Bitergia
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
# along with this program; if not, write to the Free Software
# Foundation, 51 Franklin Street, Fifth Floor, Boston, MA 02110-1335, USA.
#
# Authors:
#     Alvaro del Castillo <acs@bitergia.com>

import logging
import sys
import unittest


# Hack to make sure that tests import the right packages
# due to setuptools behaviour
sys.path.insert(0, '..')

from mordred.config import Config
from mordred.mordred import Mordred
from mordred.task_collection import TaskRawDataCollection

CONF_FILE = 'test.cfg'
PROJ_FILE = 'test-projects.json'
GIT_BACKEND_SECTION = 'git'
GIT_REPO_NAME = 'https://github.com/Bitergia/mordred.git'

logging.basicConfig(level=logging.INFO)

class TestTaskRawDataCollection(unittest.TestCase):
    """Task tests"""

    def test_initialization(self):
        """Test whether attributes are initializated"""
        config = Config(CONF_FILE)
        morderer = Mordred(config)
        repos = [GIT_REPO_NAME]
        backend_section = GIT_BACKEND_SECTION
        task = TaskRawDataCollection(morderer.conf, repos=repos, backend_section=backend_section)

        self.assertEqual(task.conf, morderer.conf)
        self.assertEqual(task.repos, repos)
        self.assertEqual(task.backend_section, backend_section)

    def test_run(self):
        """Test whether the Task could be run"""
        config = Config(CONF_FILE)
        morderer = Mordred(config)
        repos = [GIT_REPO_NAME]
        backend_section = GIT_BACKEND_SECTION
        task = TaskRawDataCollection(morderer.conf, repos=repos, backend_section=backend_section)
        self.assertEqual(task.execute(), None)


if __name__ == "__main__":
    unittest.main(warnings='ignore')
