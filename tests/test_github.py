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
#     Luis Cañas-Díaz <lcanas@bitergia.com>
#


import sys
import unittest


# Hack to make sure that tests import the right packages
# due to setuptools behaviour
sys.path.insert(0, '..')

import configparser

from sirmordred.error import GithubFileNotFound
from sirmordred.github import Github

CONF_FILE = 'test.cfg'


class TestGithub(unittest.TestCase):
    """Task tests"""

    def test_read_file(self):
        config = configparser.ConfigParser()
        config.read(CONF_FILE)

        uri = 'https://github.com/grimoirelab/GrimoireELK/blob/master/README.md'

        token = config.get('github', 'api-token')

        gh = Github(token)

        self.assertIsInstance(gh.read_file_from_uri(uri), str)
        self.assertTrue(len(gh.read_file_from_uri(uri)) > 0)

        uri = 'https://github.com/grimoirelab/doesnotexist/blob/master/README.md'
        self.assertRaises(GithubFileNotFound, gh.read_file_from_uri, uri)

        uri = 'https://twitter.com/bitergia'
        self.assertRaises(GithubFileNotFound, gh.read_file_from_uri, uri)


if __name__ == "__main__":
    unittest.main(warnings='ignore')
