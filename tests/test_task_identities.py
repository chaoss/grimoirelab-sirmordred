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


import json
import sys
import unittest

# Hack to make sure that tests import the right packages
# due to setuptools behaviour
sys.path.insert(0, '..')

from sgqlc.operation import Operation

from grimoire_elk.enriched.sortinghat_gelk import SortingHat

from sirmordred.config import Config
from sirmordred.task_identities import TaskIdentitiesMerge

from sortinghat.cli.client import SortingHatClient, SortingHatSchema


CONF_FILE = 'test.cfg'
REMOTE_IDENTITIES_FILE = 'data/remote_identities_sortinghat.json'
# REMOTE_IDENTITIES_FILE_URL = 'http://example.com/identities.json'
REMOTE_IDENTITIES_FILE_URL = 'https://github.com/fake/repo/identities.json'


def read_file(filename, mode='r'):
    with open(filename, mode) as f:
        content = f.read()
    return content


class TestTaskIdentitiesMerge(unittest.TestCase):
    """Task tests"""

    def _setup(self, conf_file):
        self.config = Config(conf_file)
        self.conf = self.config.get_conf()
        sh = self.conf.get('sortinghat')
        self.sortinghat_client = SortingHatClient(host=sh['host'], port=sh.get('port', None),
                                                  path=sh.get('path', None), ssl=sh.get('ssl', False),
                                                  user=sh['user'], password=sh['password'],
                                                  verify_ssl=sh.get('verify_ssl', True),
                                                  tenant=sh.get('tenant', True))
        self.sortinghat_client.connect()

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

    @staticmethod
    def add_identity(task, args):
        op = Operation(SortingHatSchema.SortingHatMutation)
        identity = op.add_identity(**args)
        identity.uuid()
        task.client.execute(op)

    @staticmethod
    def add_organization(task, args):
        op = Operation(SortingHatSchema.SortingHatMutation)
        org = op.add_organization(**args)
        org.organization.name()
        task.client.execute(op)

    @staticmethod
    def add_domain(task, args):
        op = Operation(SortingHatSchema.SortingHatMutation)
        dom = op.add_domain(**args)
        dom.domain.domain()
        task.client.execute(op)

    def setUp(self):
        self._setup(CONF_FILE)
        task = TaskIdentitiesMerge(self.config, self.sortinghat_client)

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

        data = json.loads(read_file("data/task-identities-data.json"))

        identities = data['identities']
        for identity in identities:
            self.add_identity(task, identity)

        organizations = data['organizations']
        for org in organizations:
            self.add_organization(task, {"name": org['organization']})
            self.add_domain(task, org)

    def test_initialization(self):
        """Test whether attributes are initializated"""

        self._setup(CONF_FILE)
        task = TaskIdentitiesMerge(self.config, self.sortinghat_client)

        self.assertEqual(task.config, self.config)

    def test_is_backend_task(self):
        self._setup(CONF_FILE)
        task = TaskIdentitiesMerge(self.config, self.sortinghat_client)

        self.assertFalse(task.is_backend_task())

    def test_execute(self):
        self._setup(CONF_FILE)
        task = TaskIdentitiesMerge(self.config, self.sortinghat_client)

        self.assertIsNone(task.execute())
        args = {
            'page': 1,
            'page_size': 10
        }
        op = Operation(SortingHatSchema.Query)
        op.individuals(**args)
        individual = op.individuals().entities()
        individual.profile().name()
        individual.enrollments().group().name()
        result = task.client.execute(op)
        entities = result['data']['individuals']['entities']

        enrolls = {}
        for e in entities:
            name = e['profile']['name']
            enroll = e['enrollments'][0]['group']['name']
            if name in enrolls:
                enrolls[name].append(enroll)
            else:
                enrolls[name] = [enroll]

        expected_enrolls = {
            "user2": ["org2"],
            "user3": ["org1"],
            "user4": ["org2", "org3"],
            "user6": ["org6"],
            "user7": ["org1"],
            "user8": ["org8"],
            "user9": ["org2"],
            "user10": ["org3"]
        }

        self.assertDictEqual(enrolls, expected_enrolls)
        self.assertEqual(len(entities), 9)


if __name__ == "__main__":
    # logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')
    unittest.main(buffer=True, warnings='ignore')
