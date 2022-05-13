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
#     Alvaro del Castillo <acs@bitergia.com>


import os
import json
import sys
import unittest


# Hack to make sure that tests import the right packages
# due to setuptools behaviour
sys.path.insert(0, '..')

from sirmordred.config import Config
from sirmordred.task import Task

CONF_FILE = 'test.cfg'
BACKEND_NAME = 'stackexchange'
COLLECTION_URL_STACKEXCHANGE = 'http://127.0.0.1:9200'
REPO_NAME = 'https://stackoverflow.com/questions/tagged/ovirt'


def read_file(filename, mode='r'):
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), filename), mode) as f:
        content = f.read()
    return content


class TestTask(unittest.TestCase):
    """Task tests"""

    def test_initialization(self):
        """Test whether attributes are initializated"""

        config = Config(CONF_FILE)
        task = Task(config)

        self.assertEqual(task.config, config)
        self.assertEqual(task.db_sh, task.conf['sortinghat']['database'])
        self.assertEqual(task.db_user, task.conf['sortinghat']['user'])
        self.assertEqual(task.db_password, task.conf['sortinghat']['password'])
        self.assertEqual(task.db_host, task.conf['sortinghat']['host'])

    def test_run(self):
        """Test whether the Task could be run"""

        config = Config(CONF_FILE)
        task = Task(config)
        self.assertEqual(task.execute(), None)

    def test_compose_p2o_params(self):
        """Test whether p2o params are built correctly for a backend and a repository"""

        config = Config(CONF_FILE)
        task = Task(config)
        params = task._compose_p2o_params("stackexchange", "https://stackoverflow.com/questions/tagged/example")
        self.assertDictEqual(params, {'url': "https://stackoverflow.com/questions/tagged/example"})

        params = task._compose_p2o_params("mediawiki",
                                          "https://wiki-archive.opendaylight.org "
                                          "https://wiki-archive.opendaylight.org/view")
        self.assertDictEqual(params, {'url': "https://wiki-archive.opendaylight.org "
                                             "https://wiki-archive.opendaylight.org/view"})

        params = task._compose_p2o_params("mediawiki",
                                          "https://wiki-archive.opendaylight.org "
                                          "https://wiki-archive.opendaylight.org/view "
                                          "--filter-no-collection=true")
        self.assertDictEqual(params, {'url': "https://wiki-archive.opendaylight.org "
                                             "https://wiki-archive.opendaylight.org/view",
                                      "filter-no-collection": "true"})

    def test_extract_repo_tags(self):
        """Test the extraction of tags in repositories"""

        config = Config(CONF_FILE)
        task = Task(config)
        url, tags = task._extract_repo_tags("git", "https://github.com/zhquan_example/repo --labels=[ENG, SUPP]")
        self.assertEqual(url, "https://github.com/zhquan_example/repo")
        self.assertListEqual(tags, ["ENG", "SUPP"])

        # By default it extracts '--labels'
        url, tags = task._extract_repo_tags("confluence", "https://example.com --spaces=[HOME]")
        self.assertEqual(url, "https://example.com --spaces=[HOME]")
        self.assertListEqual(tags, [])

        # To extracts '--spaces' add tag_type='spaces'
        url, tags = task._extract_repo_tags("confluence", "https://example.com --spaces=[HOME]", tag_type="spaces")
        self.assertEqual(url, "https://example.com")
        self.assertListEqual(tags, ["HOME"])

    def test_compose_perceval_params(self):
        """Test whether perceval params are built correctly for a backend and a repository"""

        expected_repo_params = json.loads(read_file('data/task-params-expected'))

        config = Config(CONF_FILE)
        task = Task(config)

        for backend in expected_repo_params.keys():
            repo = expected_repo_params.get(backend)['repo']
            perceval_params = task._compose_perceval_params(backend, repo)
            expected_params = expected_repo_params.get(backend)['params']

            self.assertEqual(expected_params.sort(), perceval_params.sort())

    def test_get_collection_url(self):
        """Test whether the collection url could be overwritten in a backend"""

        config = Config(CONF_FILE)
        task = Task(config)
        task.backend_section = "stackexchange"

        self.assertEqual(task._get_collection_url(), COLLECTION_URL_STACKEXCHANGE)


if __name__ == "__main__":
    unittest.main(warnings='ignore')
