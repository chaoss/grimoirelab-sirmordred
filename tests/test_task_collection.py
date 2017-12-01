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
import shutil
import tarfile
import unittest

from os.path import expanduser, isdir, join

# Hack to make sure that tests import the right packages
# due to setuptools behaviour
sys.path.insert(0, '..')

from mordred.config import Config
from mordred.task_collection import TaskRawDataCollection

CONF_FILE = 'test.cfg'
PROJ_FILE = 'test-projects.json'
PERCEVAL_CACHE_FILE = './cache-test.tgz'
HOME_USER = expanduser("~")
PERCEVAL_CACHE = join(HOME_USER, '.perceval')
GIT_BACKEND_SECTION = 'git'

logging.basicConfig(level=logging.INFO)


class TestTaskRawDataCollection(unittest.TestCase):
    """Task tests"""

    @classmethod
    def setUpClass(cls):
        cls.__install_perceval_cache()

    @classmethod
    def tearDownClass(cls):
        cls.__restore_perceval_cache()

    @classmethod
    def __install_perceval_cache(cls):
        logging.info("Installing the perceval cache")
        # First backup the current cache
        if isdir(PERCEVAL_CACHE + ".orig"):
            logging.error("Test cache backup exists in %s", PERCEVAL_CACHE + ".orig")
            raise RuntimeError("Environment not clean. Can't continue")

        try:
            shutil.move(PERCEVAL_CACHE, PERCEVAL_CACHE + ".orig")
        except FileNotFoundError:
            logging.warning("Perceval cache does not exists")

        tfile = tarfile.open(PERCEVAL_CACHE_FILE, 'r:gz')
        # The cache is extracted in the default place perceval uses
        # We must use a different place but it is not easy to change that
        # because it is not configurable now in TaskRawDataCollection
        tfile.extractall("/tmp")
        shutil.move("/tmp/perceval-cache", PERCEVAL_CACHE)
        logging.info("Installed the perceval cache in %s", PERCEVAL_CACHE)

    @classmethod
    def __restore_perceval_cache(self):
        logging.info("Restoring the perceval cache")
        shutil.rmtree(PERCEVAL_CACHE)
        try:
            shutil.move(PERCEVAL_CACHE + ".orig", PERCEVAL_CACHE)
        except FileNotFoundError:
            logging.warning("Perceval cache did not exists")

    def test_initialization(self):
        """Test whether attributes are initializated"""
        config = Config(CONF_FILE)
        backend_section = GIT_BACKEND_SECTION
        task = TaskRawDataCollection(config, backend_section=backend_section)

        self.assertEqual(task.config, config)
        self.assertEqual(task.backend_section, backend_section)

    def test_run(self):
        """Test whether the Task could be run"""
        config = Config(CONF_FILE)
        backend_section = GIT_BACKEND_SECTION
        task = TaskRawDataCollection(config, backend_section=backend_section)
        self.assertEqual(task.execute(), None)


if __name__ == "__main__":
    unittest.main(warnings='ignore')
