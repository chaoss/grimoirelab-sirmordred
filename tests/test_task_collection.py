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

from os.path import expanduser, join

# Hack to make sure that tests import the right packages
# due to setuptools behaviour
sys.path.insert(0, '..')

from mordred.config import Config
from mordred.task_collection import TaskRawDataCollection
from mordred.task_projects import TaskProjects

CONF_FILE = 'test.cfg'
PROJ_FILE = 'test-projects.json'
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
        backend_section = GIT_BACKEND_SECTION
        task = TaskRawDataCollection(config, backend_section=backend_section)
        # We need to load the projects
        TaskProjects(config).execute()
        self.assertEqual(task.execute(), None)

    def test_execute_from_archive(self):
        """Test fetching data from archives"""

        # proj_file -> 'test-projects-archive.json' stored within the conf file
        conf_file = 'archive-test.cfg'
        config = Config(conf_file)

        backend_sections = ['askbot', 'bugzilla', 'bugzillarest', 'confluence',
                            'discourse', 'dockerhub', 'gerrit', 'github', 'jenkins',
                            'jira', 'mediawiki', 'meetup', 'mozillaclub', 'nntp', 'phabricator',
                            'redmine', 'rss', 'stackexchange', 'slack', 'telegram']

        for backend_section in backend_sections:
            task = TaskRawDataCollection(config, backend_section=backend_section)
            # We need to load the projects
            TaskProjects(config).execute()
            self.assertEqual(task.execute(), None)


if __name__ == "__main__":
    unittest.main(warnings='ignore')
