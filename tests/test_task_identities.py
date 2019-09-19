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

import sys
import unittest

import httpretty

from sortinghat import api
from sortinghat.db.database import Database

# Hack to make sure that tests import the right packages
# due to setuptools behaviour
sys.path.insert(0, '..')

from sirmordred.config import Config
from sirmordred.task_identities import (TaskIdentitiesLoad,
                                        TaskIdentitiesMerge,
                                        logger)


CONF_FILE = 'test.cfg'
REMOTE_IDENTITIES_FILE = 'data/remote_identities_sortinghat.json'
# REMOTE_IDENTITIES_FILE_URL = 'http://example.com/identities.json'
REMOTE_IDENTITIES_FILE_URL = 'https://github.com/fake/repo/identities.json'


def read_file(filename, mode='r'):
    with open(filename, mode) as f:
        content = f.read()
    return content


def setup_http_server():
    remote_identities = read_file(REMOTE_IDENTITIES_FILE)

    http_requests = []

    def request_callback(method, uri, headers):
        last_request = httpretty.last_request()

        if uri.startswith(REMOTE_IDENTITIES_FILE_URL):
            body = remote_identities
        http_requests.append(last_request)

        return 200, headers, body

    httpretty.register_uri(httpretty.GET,
                           REMOTE_IDENTITIES_FILE_URL,
                           responses=[
                               httpretty.Response(body=request_callback)
                           ])

    return http_requests


class TestTaskIdentitiesLoad(unittest.TestCase):
    """Task tests"""

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

    def test_initialization(self):
        """Test whether attributes are initializated"""

        config = Config(CONF_FILE)
        task = TaskIdentitiesLoad(config)

        self.assertEqual(task.config, config)

    @httpretty.activate
    # This test fails in Travis with Lost connection to MySQL server during query (err: 2013)
    def off_test_load_orgs(self):
        """ Test loading of orgs in SH """
        setup_http_server()

        config = Config(CONF_FILE)
        task = TaskIdentitiesLoad(config)
        task.execute()
        # Check the number of orgs loaded
        norgs = len(api.registry(self.sh_db))
        self.assertEqual(norgs, 20)

    # @httpretty.activate
    # TODO: remote loading
    def test_identities_load_file(self):
        """ Check the local loading of identities files """
        setup_http_server()

        config = Config(CONF_FILE)
        task = TaskIdentitiesLoad(config)

        with self.assertLogs(logger, level='INFO') as cm:
            task.execute()
            self.assertEqual(cm.output[0],
                             'INFO:sirmordred.task_identities:[sortinghat] '
                             'Loading orgs from file data/orgs_sortinghat.json')
            self.assertEqual(cm.output[1],
                             'INFO:sirmordred.task_identities:[sortinghat] 20 organizations loaded')
            self.assertEqual(cm.output[2],
                             'INFO:sirmordred.task_identities:[sortinghat] '
                             'Loading identities from file data/perceval_identities_sortinghat.json')
        # Check the number of identities loaded from local and remote files
        nuids = len(api.unique_identities(self.sh_db))
        self.assertEqual(nuids, 4)

        with self.assertLogs(logger, level='INFO') as cm:
            task.execute()
            self.assertEqual(cm.output[0],
                             'INFO:sirmordred.task_identities:[sortinghat] No changes in '
                             'file data/orgs_sortinghat.json, organizations won\'t be loaded')
            self.assertEqual(cm.output[1],
                             'INFO:sirmordred.task_identities:[sortinghat] No changes in '
                             'file data/perceval_identities_sortinghat.json, identities won\'t be loaded')

    class TestTaskIdentitiesMerge(unittest.TestCase):
        """Task tests"""

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

        def test_initialization(self):
            """Test whether attributes are initializated"""

            config = Config(CONF_FILE)
            task = TaskIdentitiesMerge(config)

            self.assertEqual(task.config, config)

        def test_autogender(self):
            """Test whether autogender SH command is executed"""

            config = Config(CONF_FILE)
            # Test default value
            self.assertEqual(config.get_conf()['sortinghat']['gender'], False)
            config.get_conf()['sortinghat']['gender'] = True

            # Load some identities
            task = TaskIdentitiesLoad(config)
            task.execute()
            # Check the number of identities loaded from local and remote files
            uids = api.unique_identities(self.sh_db)

            task = TaskIdentitiesMerge(config)
            self.assertEqual(task.do_autogender(), None)

            uids = api.unique_identities(self.sh_db)

            found_genders = [uid.profile.gender for uid in uids]
            expected_genders = ['male', 'female', 'male', 'male']

            self.assertEqual(found_genders, expected_genders)


if __name__ == "__main__":
    # logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')
    unittest.main(buffer=True, warnings='ignore')
