#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2021 Bitergia
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
#     Quan Zhou <quan@bitergia.com>
#


import logging
import sys
import unittest

import requests

# Hack to make sure that tests import the right packages
# due to setuptools behaviour
sys.path.insert(0, '..')

from grimoire_elk.enriched.sortinghat_gelk import SortingHat

from sirmordred.config import Config
from sirmordred.error import DataEnrichmentError
from sirmordred.task_projects import TaskProjects
from sirmordred.task_collection import TaskRawDataCollection
from sirmordred.task_enrich import TaskEnrich

from sortinghat.cli.client import SortingHatClient, SortingHatSchema

from sgqlc.operation import Operation


CONF_FILE = 'test.cfg'
CONF_FILE_NO_SH = 'test-no-sh.cfg'
PROJ_FILE = 'test-projects.json'
GIT_BACKEND_SECTION = 'git'

logging.basicConfig(level=logging.INFO)


def read_file(filename, mode='r'):
    with open(filename, mode) as f:
        content = f.read()
    return content


class TestTaskEnrich(unittest.TestCase):
    """Task tests"""

    def _setup(self, conf_file):
        self.config = Config(conf_file)
        self.conf = self.config.get_conf()
        sh = self.conf.get('sortinghat', None)
        if sh:
            self.sortinghat_client = SortingHatClient(host=sh['host'], port=sh.get('port', None),
                                                      path=sh.get('path', None), ssl=sh.get('ssl', False),
                                                      user=sh['user'], password=sh['password'],
                                                      verify_ssl=sh.get('verify_ssl', True),
                                                      tenant=sh.get('tenant', True))
            self.sortinghat_client.connect()
        else:

            self.sortinghat_client = None

    @staticmethod
    def get_organizations(task):
        args = {
            "page": 1,
            "page_size": 10
        }
        op = Operation(SortingHatSchema.Query)
        org = op.organizations(**args)
        org.entities().name()
        result = task.client.execute(op)
        organizations = result['data']['organizations']['entities']

        return organizations

    @staticmethod
    def delete_identity(task, args):
        op = Operation(SortingHatSchema.SortingHatMutation)
        identity = op.delete_identity(**args)
        identity.uuid()
        task.client.execute(op)

    @staticmethod
    def delete_organization(task, args):
        op = Operation(SortingHatSchema.SortingHatMutation)
        org = op.delete_organization(**args)
        org.organization.name()
        task.client.execute(op)

    def setUp(self):
        self._setup(CONF_FILE)
        task = TaskEnrich(self.config, self.sortinghat_client)

        # Clean database
        # Remove identities
        entities = SortingHat.unique_identities(task.client)
        mks = [e['mk'] for e in entities]
        for i in mks:
            arg = {
                'uuid': i
            }
            self.delete_identity(task, arg)

        # Remove organization
        organizations = self.get_organizations(task)
        for org in organizations:
            self.delete_organization(task, org)

    def test_initialization(self):
        """Test whether attributes are initializated"""

        self._setup(CONF_FILE)
        backend_section = GIT_BACKEND_SECTION
        task = TaskEnrich(self.config, self.sortinghat_client, backend_section=backend_section)

        self.assertEqual(task.config, self.config)
        self.assertEqual(task.backend_section, backend_section)

    def test_select_aliases(self):
        self._setup(CONF_FILE)
        cfg = self.conf
        # We need to load the projects
        task = TaskEnrich(self.config, self.sortinghat_client)
        expected_aliases = [
            'git',
            'git_author',
            'git_enrich',
            'affiliations'
        ]
        aliases = task.select_aliases(cfg, GIT_BACKEND_SECTION)
        self.assertListEqual(aliases, expected_aliases)

    def test_retain_identities(self):
        """"""

        self._setup(CONF_FILE)
        cfg = self.conf

        # Remove old enriched index
        es_enrichment = cfg['es_enrichment']['url']
        enrich_index = es_enrichment + "/" + cfg[GIT_BACKEND_SECTION]['enriched_index']
        requests.delete(enrich_index, verify=False)

        # We need to load the projects
        TaskProjects(self.config, self.sortinghat_client).execute()
        backend_section = GIT_BACKEND_SECTION

        # Create raw data
        task_collection = TaskRawDataCollection(self.config, backend_section=backend_section)
        task_collection.execute()

        # Create enriched data
        task = TaskEnrich(self.config, self.sortinghat_client, backend_section=backend_section)
        self.assertEqual(task.execute(), None)

        entities_before = SortingHat.unique_identities(task.client)

        # No retain
        self.assertEqual(task.retain_identities(None), None)
        entities_after = SortingHat.unique_identities(task.client)
        self.assertEqual(len(entities_before), len(entities_after))

        # when the value is negative
        self.assertEqual(task.retain_identities(-1), None)
        entities_after = SortingHat.unique_identities(task.client)
        self.assertEqual(len(entities_before), len(entities_after))

        # import time
        # time.sleep(1)
        # 1 second
        retention_time = 0.016667
        task.retain_identities(retention_time)
        entities_after = SortingHat.unique_identities(task.client)
        self.assertGreater(len(entities_before), len(entities_after))

    def test_execute_retain_data(self):
        self._setup(CONF_FILE)
        cfg = self.conf
        # We need to load the projects
        TaskProjects(self.config, self.sortinghat_client).execute()
        backend_section = GIT_BACKEND_SECTION
        # Create raw data
        task_collection = TaskRawDataCollection(self.config, backend_section=backend_section)
        task_collection.execute()

        # Test enriched data
        task = TaskEnrich(self.config, self.sortinghat_client, backend_section=backend_section)
        task.execute()

        es_enrichment = cfg['es_enrichment']['url']
        enrich_index = es_enrichment + "/" + cfg[GIT_BACKEND_SECTION]['enriched_index']

        r = requests.get(enrich_index + "/_search?size=0", verify=False)
        total = r.json()['hits']['total']
        enriched_items_before = total['value'] if isinstance(total, dict) else total

        # 1 year
        retention_time = 525600
        cfg.set_param('general', 'retention_time', retention_time)
        task.execute()

        r = requests.get(enrich_index + "/_search?size=0", verify=False)
        total = r.json()['hits']['total']
        enriched_items_after = total['value'] if isinstance(total, dict) else total

        self.assertGreater(enriched_items_before, enriched_items_after)

    def test_execute(self):
        """Test whether the Task could be run"""

        self._setup(CONF_FILE)
        cfg = self.conf
        # We need to load the projects
        TaskProjects(self.config, self.sortinghat_client).execute()
        backend_section = GIT_BACKEND_SECTION

        # Create raw data
        task_collection = TaskRawDataCollection(self.config, backend_section=backend_section)
        task_collection.execute()

        # Test enriched data
        task = TaskEnrich(self.config, self.sortinghat_client, backend_section=backend_section)
        self.assertEqual(task.execute(), None)

        # Check that the enrichment went well
        es_collection = cfg['es_collection']['url']
        es_enrichment = cfg['es_enrichment']['url']
        raw_index = es_collection + "/" + cfg[GIT_BACKEND_SECTION]['raw_index']
        enrich_index = es_enrichment + "/" + cfg[GIT_BACKEND_SECTION]['enriched_index']

        r = requests.get(raw_index + "/_search?size=0", verify=False)
        total = r.json()['hits']['total']
        raw_items = total['value'] if isinstance(total, dict) else total
        r = requests.get(enrich_index + "/_search?size=0", verify=False)
        total = r.json()['hits']['total']
        enriched_items = total['value'] if isinstance(total, dict) else total

        self.assertEqual(raw_items, enriched_items)

    def test_execute_no_sh(self):
        """Test whether the Task could be run without SortingHat"""

        self._setup(CONF_FILE_NO_SH)
        cfg = self.conf
        # We need to load the projects
        TaskProjects(self.config, self.sortinghat_client).execute()
        backend_section = GIT_BACKEND_SECTION

        # Create raw data
        task_collection = TaskRawDataCollection(self.config, backend_section=backend_section)
        task_collection.execute()

        # Test enriched data
        task = TaskEnrich(self.config, self.sortinghat_client, backend_section=backend_section)
        self.assertEqual(task.execute(), None)

        # Check that the enrichment went well
        es_collection = cfg['es_collection']['url']
        es_enrichment = cfg['es_enrichment']['url']
        raw_index = es_collection + "/" + cfg[GIT_BACKEND_SECTION]['raw_index']
        enrich_index = es_enrichment + "/" + cfg[GIT_BACKEND_SECTION]['enriched_index']

        r = requests.get(raw_index + "/_search?size=0", verify=False)
        total = r.json()['hits']['total']
        raw_items = total['value'] if isinstance(total, dict) else total

        r = requests.get(enrich_index + "/_search?size=0", verify=False)
        total = r.json()['hits']['total']
        enriched_items = total['value'] if isinstance(total, dict) else total

        self.assertEqual(raw_items, enriched_items)

    def test_studies(self):
        """Test whether the studies configuration works """
        self._setup(CONF_FILE)
        cfg = self.conf
        # We need to load the projects
        TaskProjects(self.config, self.sortinghat_client).execute()
        backend_section = GIT_BACKEND_SECTION
        task = TaskEnrich(self.config, self.sortinghat_client, backend_section=backend_section)

        # Configure no studies
        cfg.set_param('git', 'studies', None)
        self.assertEqual(task.execute(), None)

        # Configure no studies
        cfg.set_param('git', 'studies', [])
        self.assertEqual(task.execute(), None)

        # Configure a wrong study
        cfg.set_param('git', 'studies', ['bad_study'])
        with self.assertRaises(DataEnrichmentError):
            self.assertEqual(task.execute(), None)

        # Configure several studies
        cfg.set_param('git', 'studies', ['enrich_onion'])
        self.assertEqual(task.execute(), None)

        # Configure several studies
        cfg.set_param('git', 'studies', ['enrich_demography:1', 'enrich_areas_of_code'])
        self.assertEqual(task.execute(), None)

        # Configure kafka kip study
        cfg.set_param('mbox', 'studies', ['kafka_kip'])
        self.assertEqual(task.execute(), None)

        # Configure several studies, one wrong
        cfg.set_param('git', 'studies', ['enrich_demography:1', "enrich_areas_of_code1"])
        with self.assertRaises(DataEnrichmentError):
            self.assertEqual(task.execute(), None)

    def test_execute_from_archive(self):
        """Test fetching data from archives"""

        # proj_file -> 'test-projects-archive.json' stored within the conf file
        conf_file = 'archives-test.cfg'
        self._setup(conf_file)

        backend_sections = ['askbot', 'bugzilla', 'bugzillarest', 'confluence',
                            'discourse', 'dockerhub', 'gerrit', 'github:issue', 'github:pull',
                            'gitlab:issue', 'gitlab:merge', 'google_hits', 'jenkins',
                            'jira', 'mediawiki', 'meetup', 'mozillaclub', 'nntp', 'phabricator',
                            'redmine', 'remo', 'rss', 'stackexchange', 'slack', 'telegram', 'twitter']

        # We need to load the projects
        TaskProjects(self.config, self.sortinghat_client).execute()
        for backend_section in backend_sections:
            task = TaskRawDataCollection(self.config, backend_section=backend_section)
            task.execute()

        for backend_section in backend_sections:
            task = TaskEnrich(self.config, self.sortinghat_client, backend_section=backend_section)
            self.assertEqual(task.execute(), None)


if __name__ == "__main__":
    unittest.main(warnings='ignore')
