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

import httpretty

from sortinghat import api
from sortinghat.db.database import Database

# Hack to make sure that tests import the right packages
# due to setuptools behaviour
sys.path.insert(0, '..')

from mordred.config import Config
from mordred.task_identities import TaskIdentitiesLoad


CONF_FILE = 'test.cfg'
REMOTE_IDENTITIES_FILE = 'data/remote_identities_sortinghat.json'
REMOTE_IDENTITIES_FILE_URL = 'http://example.com/identities.json'


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

        return (200, headers, body)

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
        self.sh_db = Database(**self.sh_kwargs)

    def test_initialization(self):
        """Test whether attributes are initializated"""

        config = Config(CONF_FILE)
        task = TaskIdentitiesLoad(config)

        self.assertEqual(task.config, config)

    @httpretty.activate
    def test_load_orgs(self):
        """ Test loading of orgs in SH """
        setup_http_server()

        config = Config(CONF_FILE)
        config.set_param("sortinghat", "load_orgs", True)
        config.set_param("sortinghat", "orgs_file", None)
        task = TaskIdentitiesLoad(config)
        with self.assertRaises(RuntimeError):
            task.execute()
        config = Config(CONF_FILE)
        task = TaskIdentitiesLoad(config)
        task.execute()
        # Check the number of orgs loaded
        norgs = len(api.registry(self.sh_db))
        self.assertEqual(norgs, 20)

    @httpretty.activate
    def test_identities_load_file(self):
        """ Check the local and remote loading of identities files """
        setup_http_server()

        config = Config(CONF_FILE)
        task = TaskIdentitiesLoad(config)
        task.execute()
        # Check the number of identities loaded from local and remote files
        nuids = len(api.unique_identities(self.sh_db))
        self.assertEqual(nuids, 18)


if __name__ == "__main__":
    # logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')
    unittest.main(buffer=True, warnings='ignore')
