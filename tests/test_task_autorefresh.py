# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 Bitergia
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
#     Jose Javier Merchante <jjmerchante@bitergia.com>
#

import json
import logging
import sys
import unittest

import requests

# Hack to make sure that tests import the right packages
# due to setuptools behaviour
sys.path.insert(0, '..')


from grimoire_elk.enriched.sortinghat_gelk import SortingHat

from sirmordred.config import Config
from sirmordred.task_autorefresh import TaskAutorefresh
from sirmordred.task_collection import TaskRawDataCollection
from sirmordred.task_enrich import TaskEnrich
from sirmordred.task_projects import TaskProjects

from sortinghat.cli.client import SortingHatSchema

from sgqlc.operation import Operation


CONF_FILE = 'test.cfg'
GIT_BACKEND_SECTION = 'git'


logging.basicConfig(level=logging.INFO)


def read_file(filename, mode='r'):
    with open(filename, mode) as f:
        content = f.read()
    return content


class TestTaskAutorefresh(unittest.TestCase):
    """Test TaskAutorefresh"""

    @staticmethod
    def get_organizations(client):
        args = {
            "page": 1,
            "page_size": 10
        }
        op = Operation(SortingHatSchema.Query)
        org = op.organizations(**args)
        org.entities().name()
        result = client.execute(op)
        organizations = result['data']['organizations']['entities']

        return organizations

    @staticmethod
    def get_individuals(client):
        args = {
            "page": 1,
            "page_size": 1000
        }
        op = Operation(SortingHatSchema.Query)
        individual = op.individuals(**args)
        individual.entities().mk()
        individual.entities().profile().name()
        result = client.execute(op)

        return result['data']['individuals']['entities']

    @staticmethod
    def delete_identity(client, args):
        op = Operation(SortingHatSchema.SortingHatMutation)
        identity = op.delete_identity(**args)
        identity.uuid()
        client.execute(op)

    @staticmethod
    def delete_organization(client, args):
        op = Operation(SortingHatSchema.SortingHatMutation)
        org = op.delete_organization(**args)
        org.organization.name()
        client.execute(op)

    @staticmethod
    def merge_individuals(client, args):
        op = Operation(SortingHatSchema.SortingHatMutation)
        merge = op.merge(**args)
        merge.individual().mk()
        client.execute(op)

    @staticmethod
    def add_identity(client, args):
        op = Operation(SortingHatSchema.SortingHatMutation)
        identity = op.add_identity(**args)
        identity.uuid()
        client.execute(op)

    @staticmethod
    def add_organization(client, args):
        op = Operation(SortingHatSchema.SortingHatMutation)
        org = op.add_organization(**args)
        org.organization.name()
        client.execute(op)

    @staticmethod
    def add_domain(client, args):
        op = Operation(SortingHatSchema.SortingHatMutation)
        dom = op.add_domain(**args)
        dom.domain.domain()
        client.execute(op)

    def setUp(self):
        config = Config(CONF_FILE)
        task = TaskAutorefresh(config)

        # Clean database
        entities = SortingHat.unique_identities(task.client)
        mks = [e['mk'] for e in entities]
        for i in mks:
            arg = {
                'uuid': i
            }
            self.delete_identity(task.client, arg)

        organizations = self.get_organizations(task.client)
        for org in organizations:
            self.delete_organization(task.client, org)

        # Add identities and organizations
        data = json.loads(read_file("data/task-identities-data.json"))

        identities = data['identities']
        for identity in identities:
            self.add_identity(task.client, identity)

        organizations = data['organizations']
        for org in organizations:
            self.add_organization(task.client, {"name": org['organization']})
            self.add_domain(task.client, org)

    def test_initialization(self):
        """Test whether attributes are initialized"""

        config = Config(CONF_FILE)
        task = TaskAutorefresh(config)

        self.assertEqual(task.config, config)

    def test_is_backend_task(self):
        """Test whether the Task is not a backend task"""

        config = Config(CONF_FILE)
        task = TaskAutorefresh(config)

        self.assertFalse(task.is_backend_task())

    def test_execute(self):
        """Test whether the Task could be run"""

        # Create a raw and enriched indexes
        config = Config(CONF_FILE)

        TaskProjects(config).execute()
        backend_section = GIT_BACKEND_SECTION

        task_collection = TaskRawDataCollection(config, backend_section=backend_section)
        task_collection.execute()

        task_enrich = TaskEnrich(config, backend_section=backend_section)
        task_enrich.execute()

        task_autorefresh = TaskAutorefresh(config)
        task_autorefresh.config.set_param('es_enrichment', 'autorefresh', True)
        # This does nothing because it uses now as from_date:
        task_autorefresh.execute()

        # Merge all the identities into user1
        individuals = self.get_individuals(task_autorefresh.client)
        to_uuid = '72f6fc79632080fc17dc8f83c0ddd5ff5b5e5005'
        from_uuids = [ind['mk'] for ind in individuals if ind['mk'] != to_uuid]
        arg = {'from_uuids': from_uuids, 'to_uuid': to_uuid}
        self.merge_individuals(task_autorefresh.client, arg)

        self.assertIsNone(task_autorefresh.execute())

        # Check that the autorefresh went well
        cfg = config.get_conf()
        es_enrichment = cfg['es_enrichment']['url']
        enrich_index = es_enrichment + "/" + cfg[GIT_BACKEND_SECTION]['enriched_index']

        r = requests.get(enrich_index + "/_search", verify=False)
        for hit in r.json()['hits']['hits']:
            self.assertEqual(hit['_source']['author_uuid'], to_uuid)


if __name__ == "__main__":
    unittest.main(buffer=True, warnings='ignore')
