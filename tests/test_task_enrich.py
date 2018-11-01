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
import sys
import unittest

import requests

from sortinghat.db.database import Database

# Hack to make sure that tests import the right packages
# due to setuptools behaviour
sys.path.insert(0, '..')

from sirmordred.config import Config
from sirmordred.error import DataEnrichmentError
from sirmordred.task_projects import TaskProjects
from sirmordred.task_collection import TaskRawDataCollection
from sirmordred.task_enrich import TaskEnrich

CONF_FILE = 'test.cfg'
CONF_FILE_NO_SH = 'test-no-sh.cfg'
PROJ_FILE = 'test-projects.json'
GIT_BACKEND_SECTION = 'git'

logging.basicConfig(level=logging.INFO)


class TestTaskEnrich(unittest.TestCase):
    """Task tests"""

    def setUp(self):
        config = Config(CONF_FILE)
        sh = config.get_conf().get('sortinghat', None)

        if not sh:
            return

        self.sh_kwargs = {'user': sh['user'], 'password': sh['password'],
                          'database': sh['database'], 'host': sh['host'],
                          'port': None}

        # Clean the database to start an empty state
        Database.drop(**self.sh_kwargs)

        # Create command
        Database.create(**self.sh_kwargs)
        self.sh_db = Database(**self.sh_kwargs)

    def test_initialization(self):
        """Test whether attributes are initializated"""

        config = Config(CONF_FILE)
        backend_section = GIT_BACKEND_SECTION
        task = TaskEnrich(config, backend_section=backend_section)

        self.assertEqual(task.config, config)
        self.assertEqual(task.backend_section, backend_section)

    def test_execute(self):
        """Test whether the Task could be run"""

        def setUp(self):
            config = Config(CONF_FILE)
            sh = config.get_conf()['sortinghat']

            self.sh_kwargs = {'user': sh['user'], 'password': sh['password'],
                              'database': sh['database'], 'host': sh['host'],
                              'port': None}

            # Clean the database to start an empty state

            Database.drop(**self.sh_kwargs)

            # Create command
            Database.create(**self.sh_kwargs)
            self.sh_db = Database(**self.sh_kwargs)

        config = Config(CONF_FILE)
        cfg = config.get_conf()
        # We need to load the projects
        TaskProjects(config).execute()
        backend_section = GIT_BACKEND_SECTION
        task = TaskEnrich(config, backend_section=backend_section)
        self.assertEqual(task.execute(), None)

        # Check that the enrichment went well
        es_collection = cfg['es_collection']['url']
        es_enrichment = cfg['es_enrichment']['url']
        raw_index = es_collection + "/" + cfg[GIT_BACKEND_SECTION]['raw_index']
        enrich_index = es_enrichment + "/" + cfg[GIT_BACKEND_SECTION]['enriched_index']

        r = requests.get(raw_index + "/_search?size=0", verify=False)
        raw_items = r.json()['hits']['total']
        r = requests.get(enrich_index + "/_search?size=0", verify=False)
        enriched_items = r.json()['hits']['total']

        self.assertEqual(raw_items, enriched_items)

    def test_execute_no_sh(self):
        """Test whether the Task could be run without SortingHat"""

        config = Config(CONF_FILE_NO_SH)
        cfg = config.get_conf()
        # We need to load the projects
        TaskProjects(config).execute()
        backend_section = GIT_BACKEND_SECTION
        task = TaskEnrich(config, backend_section=backend_section)
        self.assertEqual(task.execute(), None)

        # Check that the enrichment went well
        es_collection = cfg['es_collection']['url']
        es_enrichment = cfg['es_enrichment']['url']
        raw_index = es_collection + "/" + cfg[GIT_BACKEND_SECTION]['raw_index']
        enrich_index = es_enrichment + "/" + cfg[GIT_BACKEND_SECTION]['enriched_index']

        r = requests.get(raw_index + "/_search?size=0", verify=False)
        raw_items = r.json()['hits']['total']
        r = requests.get(enrich_index + "/_search?size=0", verify=False)
        enriched_items = r.json()['hits']['total']

        self.assertEqual(raw_items, enriched_items)

    def test_studies(self):
        """Test whether the studies configuration works """
        config = Config(CONF_FILE)
        cfg = config.get_conf()
        # We need to load the projects
        TaskProjects(config).execute()
        backend_section = GIT_BACKEND_SECTION
        task = TaskEnrich(config, backend_section=backend_section)

        # Configure no studies
        cfg['git']['studies'] = None
        self.assertEqual(task.execute(), None)

        # Configure no studies
        cfg['git']['studies'] = []
        self.assertEqual(task.execute(), None)

        # Configure a wrong study
        cfg['git']['studies'] = ['bad_study']
        with self.assertRaises(DataEnrichmentError):
            self.assertEqual(task.execute(), None)

        # Configure several studies
        cfg['git']['studies'] = ['enrich_onion']
        self.assertEqual(task.execute(), None)

        # Configure several studies
        cfg['git']['studies'] = ['enrich_demography:1', 'enrich_areas_of_code']
        self.assertEqual(task.execute(), None)

        # Configure kafka kip study
        cfg['mbox']['studies'] = ['kafka_kip']
        self.assertEqual(task.execute(), None)

        # Configure several studies, one wrong
        cfg['git']['studies'] = ['enrich_demography:1', "enrich_areas_of_code1"]
        with self.assertRaises(DataEnrichmentError):
            self.assertEqual(task.execute(), None)

    def test_execute_from_archive(self):
        """Test fetching data from archives"""

        # proj_file -> 'test-projects-archive.json' stored within the conf file
        conf_file = 'archives-test.cfg'
        config = Config(conf_file)

        backend_sections = ['askbot', 'bugzilla', 'bugzillarest', 'confluence',
                            'discourse', 'dockerhub', 'gerrit', 'github:issue', 'github:pull',
                            'gitlab:issue', 'gitlab:merge', 'google_hits', 'jenkins',
                            'jira', 'mediawiki', 'meetup', 'mozillaclub', 'nntp', 'phabricator',
                            'redmine', 'remo', 'rss', 'stackexchange', 'slack', 'telegram', 'twitter']

        # We need to load the projects
        TaskProjects(config).execute()
        for backend_section in backend_sections:
            task = TaskRawDataCollection(config, backend_section=backend_section)
            task.execute()

        for backend_section in backend_sections:
            task = TaskEnrich(config, backend_section=backend_section)
            self.assertEqual(task.execute(), None)


if __name__ == "__main__":
    unittest.main(warnings='ignore')
