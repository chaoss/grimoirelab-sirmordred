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


import logging
import requests
import sys
import unittest

from os.path import expanduser, join

# Hack to make sure that tests import the right packages
# due to setuptools behaviour
sys.path.insert(0, '..')

from sirmordred.config import Config
from sirmordred.task_collection import TaskRawDataCollection
from sirmordred.task_projects import TaskProjects

CONF_FILE = 'test.cfg'
PROJ_FILE = 'test-projects.json'

CONF_FILE_NO_COLL = 'test-no-collection.cfg'
PROJ_FILE_NO_COLL = 'test-projects-no-collection.json'

CONF_ARCHIVE_FILE = 'archives-test.cfg'

HOME_USER = expanduser("~")
PERCEVAL_ARCHIVE = join(HOME_USER, '.perceval')

GIT_BACKEND_SECTION = 'git'

GITHUB_BACKEND_SECTION = 'github'
GITHUB_REPO = "https://github.com/grimoirelab/perceval"


logging.basicConfig(level=logging.INFO)


class TestTaskRawDataCollection(unittest.TestCase):
    """Task tests"""

    def test_initialization(self):
        """Test whether attributes are initializated"""

        config = Config(CONF_FILE)
        backend_section = GIT_BACKEND_SECTION
        task = TaskRawDataCollection(config, backend_section=backend_section)

        self.assertEqual(task.config, config)
        self.assertEqual(task.backend_section, backend_section)

    def test_backend_params(self):
        """Test whether the backend parameters are initializated"""

        config = Config(CONF_FILE)
        backend_section = GITHUB_BACKEND_SECTION
        task = TaskRawDataCollection(config, backend_section=backend_section)
        params = task._compose_perceval_params(GITHUB_BACKEND_SECTION, GITHUB_REPO)

        expected_params = [
            'grimoirelab',
            'perceval',
            '--api-token',
            'XXXXX',
            '--sleep-time',
            '300',
            '--sleep-for-rate',
            '--category',
            'issue',
            '--archive-path',
            '/tmp/test_github_archive'
        ]

        self.assertEqual(len(params), len(expected_params))

        for p in params:
            self.assertTrue(p in expected_params)

    def test_execute(self):
        """Test whether the Task could be run"""

        config = Config(CONF_FILE)
        cfg = config.get_conf()
        backend_section = GIT_BACKEND_SECTION
        task = TaskRawDataCollection(config, backend_section=backend_section)
        # We need to load the projects
        TaskProjects(config).execute()
        self.assertIsNotNone(task.execute())

        # Check that the collection went well
        es_collection = cfg['es_collection']['url']
        raw_index = es_collection + "/" + cfg[GIT_BACKEND_SECTION]['raw_index']

        r = requests.get(raw_index + "/_search?size=0", verify=False)
        raw_items = r.json()['hits']['total']
        self.assertEqual(raw_items, 3603)

    def test_execute_no_collection(self):
        """Test whether the raw data is not downloaded when --filter-no-collection is true"""

        config = Config(CONF_FILE_NO_COLL)
        cfg = config.get_conf()
        backend_section = GIT_BACKEND_SECTION
        task = TaskRawDataCollection(config, backend_section=backend_section)
        # We need to load the projects
        TaskProjects(config).execute()
        self.assertIsNotNone(task.execute())

        # Check that the fitler --filter-no-collection works
        es_collection = cfg['es_collection']['url']
        raw_index = es_collection + "/" + cfg[GIT_BACKEND_SECTION]['raw_index']

        r = requests.get(raw_index + "/_search?size=0", verify=False)
        raw_items = r.json()['hits']['total']
        self.assertEqual(raw_items, 40)

    def test_execute_filter_no_collection(self):
        """Test whether the Task could be run"""

        config = Config(CONF_FILE)
        backend_section = GIT_BACKEND_SECTION
        task = TaskRawDataCollection(config, backend_section=backend_section)
        # We need to load the projects
        TaskProjects(config).execute()
        self.assertIsNotNone(task.execute())

    def test_execute_from_archive(self):
        """Test fetching data from archives"""

        # proj_file -> 'test-projects-archive.json' stored within the conf file
        config = Config(CONF_ARCHIVE_FILE)

        backend_sections = ['askbot', 'bugzilla', 'bugzillarest', 'confluence',
                            'discourse', 'dockerhub', 'gerrit', 'github:issue', 'github:pull',
                            'gitlab:issue', 'gitlab:merge', 'google_hits', 'jenkins',
                            'jira', 'mediawiki', 'meetup', 'mozillaclub', 'nntp', 'phabricator',
                            'redmine', 'remo', 'rss', 'stackexchange', 'slack', 'telegram', 'twitter']

        # We need to load the projects
        TaskProjects(config).execute()
        for backend_section in backend_sections:
            task = TaskRawDataCollection(config, backend_section=backend_section)
            errors = task.execute()
            for err in errors:
                self.assertIn('backend', err)
                self.assertIn('repo', err)
                self.assertIn('error', err)


if __name__ == "__main__":
    unittest.main(warnings='ignore')
