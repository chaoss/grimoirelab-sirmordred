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
import tempfile
import unittest


# Hack to make sure that tests import the right packages
# due to setuptools behaviour
sys.path.insert(0, '..')

from sirmordred.config import Config
from sirmordred.task import Task

from sortinghat.cli.client import SortingHatClient

CONF_FILE = 'test.cfg'
CONF_CREDENTIALS = 'test_credentials.cfg'
BACKEND_NAME = 'stackexchange'
COLLECTION_URL_STACKEXCHANGE = 'http://127.0.0.1:9200'
REPO_NAME = 'https://stackoverflow.com/questions/tagged/ovirt'
GITHUB_REPO_URL = 'https://github.com/example/repo'
GIT_REPO_URL = 'https://github.com/example/repo.git'
SECRETS_MANAGER_FLAGS = ['--secrets-manager', 'bitwarden',
                         '--secret-name', 'github-prod']


def read_file(filename, mode='r'):
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), filename), mode) as f:
        content = f.read()
    return content


class TestTask(unittest.TestCase):
    """Task tests"""
    def setUp(self):
        self.config = Config(CONF_FILE)
        self.conf = self.config.get_conf()
        sh = self.conf.get('sortinghat')
        self.sortinghat_client = SortingHatClient(host=sh['host'], port=sh.get('port', None),
                                                  path=sh.get('path', None), ssl=sh.get('ssl', False),
                                                  user=sh['user'], password=sh['password'],
                                                  verify_ssl=sh.get('verify_ssl', True),
                                                  tenant=sh.get('tenant', True))
        self.sortinghat_client.connect()

    def test_initialization(self):
        """Test whether attributes are initializated"""

        task = Task(self.config, self.sortinghat_client)

        self.assertEqual(task.config, self.config)
        self.assertEqual(task.db_sh, task.conf['sortinghat']['database'])
        self.assertEqual(task.db_user, task.conf['sortinghat']['user'])
        self.assertEqual(task.db_password, task.conf['sortinghat']['password'])
        self.assertEqual(task.db_host, task.conf['sortinghat']['host'])

    def test_run(self):
        """Test whether the Task could be run"""

        task = Task(self.config, self.sortinghat_client)
        self.assertEqual(task.execute(), None)

    def test_compose_p2o_params(self):
        """Test whether p2o params are built correctly for a backend and a repository"""

        task = Task(self.config, self.sortinghat_client)
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

        task = Task(self.config, self.sortinghat_client)
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

        task = Task(self.config, self.sortinghat_client)

        for backend in expected_repo_params.keys():
            repo = expected_repo_params.get(backend)['repo']
            perceval_params = task._compose_perceval_params(backend, repo)
            expected_params = expected_repo_params.get(backend)['params']

            self.assertEqual(expected_params.sort(), perceval_params.sort())

    def test_get_collection_url(self):
        """Test whether the collection url could be overwritten in a backend"""

        task = Task(self.config, self.sortinghat_client)
        task.backend_section = "stackexchange"

        self.assertEqual(task._get_collection_url(), COLLECTION_URL_STACKEXCHANGE)


class TestComposePercevalParamsCredentials(unittest.TestCase):
    """Tests for the secrets-manager flag emission in
    `Task._compose_perceval_params`.

    These tests do not need a live SortingHat: `_compose_perceval_params`
    never touches the client, and `Task.__init__` accepts
    `sortinghat_client=None` and reads optional [sortinghat] config from
    the fixture without opening a connection. Keeping them isolated from
    `TestTask`'s SortingHat-dependent setUp makes the new behaviour
    verifiable in any environment.
    """

    def test_secrets_manager_appended(self):
        """Flags are appended when [general] secrets_manager is set and
        the backend has a [<backend>:credentials] section."""

        config = Config(CONF_CREDENTIALS)
        task = Task(config, sortinghat_client=None)

        params = task._compose_perceval_params('github', GITHUB_REPO_URL)

        self.assertEqual(params[-4:], SECRETS_MANAGER_FLAGS)

    def test_default_item_name(self):
        """When [<backend>:credentials] omits item-name, --secret-name
        defaults to the base backend name."""

        original = read_file(CONF_CREDENTIALS)
        patched = original.replace('item-name = github-prod\n', '')
        tmp_path = tempfile.mktemp(prefix='test_credentials_', suffix='.cfg')
        with open(tmp_path, 'w') as f:
            f.write(patched)

        try:
            config = Config(tmp_path)
            task = Task(config, sortinghat_client=None)
            params = task._compose_perceval_params('github', GITHUB_REPO_URL)
            self.assertEqual(
                params[-4:],
                ['--secrets-manager', 'bitwarden', '--secret-name', 'github'],
            )
        finally:
            os.remove(tmp_path)

    def test_no_secrets_manager(self):
        """Without [general] secrets_manager set, no flags are appended
        even if a [<backend>:credentials] section happens to exist."""

        config = Config(CONF_FILE)
        task = Task(config, sortinghat_client=None)

        params = task._compose_perceval_params('github', GITHUB_REPO_URL)

        self.assertNotIn('--secrets-manager', params)
        self.assertNotIn('--secret-name', params)

    def test_no_credentials_section(self):
        """With secrets_manager set but no [<backend>:credentials], no
        flags are appended for that backend."""

        config = Config(CONF_CREDENTIALS)
        task = Task(config, sortinghat_client=None)

        # test_credentials.cfg has [git] but no [git:credentials].
        params = task._compose_perceval_params('git', GIT_REPO_URL)

        self.assertNotIn('--secrets-manager', params)
        self.assertNotIn('--secret-name', params)

    def test_parameterized_backend_uses_base(self):
        """For a parameterized backend section like 'github:pull', the
        credentials subsection is resolved against the base backend."""

        config = Config(CONF_CREDENTIALS)
        task = Task(config, sortinghat_client=None)

        params = task._compose_perceval_params('github:pull', GITHUB_REPO_URL)

        self.assertEqual(params[-4:], SECRETS_MANAGER_FLAGS)


if __name__ == "__main__":
    unittest.main(warnings='ignore')
