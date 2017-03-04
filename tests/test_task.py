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


import sys
import unittest


# Hack to make sure that tests import the right packages
# due to setuptools behaviour
sys.path.insert(0, '..')

from mordred.task import Task
from mordred.mordred import Mordred

CONF_FILE = 'test.cfg'
BACKEND_NAME = 'stackexchange'
COLLECTION_URL = 'http://localhost:9200'
COLLECTION_URL_STACKEXCHANGE = 'http://elasticsearch:9200'
REPO_NAME = 'https://stackoverflow.com/questions/tagged/ovirt'

class TestTask(unittest.TestCase):
    """Task tests"""

    def test_initialization(self):
        """Test whether attributes are initializated"""

        morderer = Mordred(CONF_FILE)
        task = Task(morderer.conf)

        self.assertEqual(task.conf, morderer.conf)
        self.assertEqual(task.db_sh, task.conf['sh_database'])
        self.assertEqual(task.db_user, task.conf['sh_user'])
        self.assertEqual(task.db_password, task.conf['sh_password'])
        self.assertEqual(task.db_host, task.conf['sh_host'])

    def test_run(self):
        """Test whether the Task could be run"""
        morderer = Mordred(CONF_FILE)
        task = Task(morderer.conf)
        self.assertEqual(task.execute(), None)

    def test_compose_p2o_params(self):
        """Test whether p2o params are built correctly for a backend and a repository"""

        morderer = Mordred(CONF_FILE)
        task = Task(morderer.conf)
        params = task._compose_p2o_params(BACKEND_NAME, REPO_NAME)
        self.assertEqual(params, {'url': REPO_NAME})

    def test_compose_perceval_params(self):
        """Test whether perceval params are built correctly for a backend and a repository"""

        morderer = Mordred(CONF_FILE)
        task = Task(morderer.conf)
        params = ['--site', 'stackoverflow.com', '--tagged', 'ovirt',
                  '--tag', 'https://stackoverflow.com/questions/tagged/ovirt',
                  '--api-token', 'token', '--fetch-cache']
        perceval_params = task._compose_perceval_params(BACKEND_NAME, REPO_NAME)
        self.assertEqual(params.sort(), perceval_params.sort())

    def test_get_collection_url(self):
        """Test whether the collection url could be overried in a backend"""
        morderer = Mordred(CONF_FILE)
        task = Task(morderer.conf)
        task.backend_section = BACKEND_NAME
        self.assertEqual(task.conf['es_collection'], COLLECTION_URL)
        self.assertEqual(task._get_collection_url(), COLLECTION_URL_STACKEXCHANGE)


if __name__ == "__main__":
    unittest.main(warnings='ignore')
