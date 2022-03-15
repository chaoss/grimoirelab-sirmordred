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


import unittest

from datetime import datetime
from unittest.mock import patch, mock_open

from sirmordred.utils.healthcheck import match_error_string, read_cache_file


class TestHealthCheck(unittest.TestCase):
    """Task tests for healthcheck.py methods"""

    def test_match_error(self):
        """Test match_error_string method in charge of finding error patterns in log lines"""

        file_path = './data/mordred.log'
        match_string = 'Exception in Task Manager'

        time_a = datetime.strptime('2019-11-27 13:50:50,425', '%Y-%m-%d %H:%M:%S,%f')
        time_b = datetime.strptime('2019-11-27 13:50:52,663', '%Y-%m-%d %H:%M:%S,%f')
        self.assertTrue(match_error_string(file_path, time_a, time_b, match_string))

        time_a = datetime.strptime('2019-11-27 13:50:50,429', '%Y-%m-%d %H:%M:%S,%f')
        self.assertFalse(match_error_string(file_path, time_a, time_b, match_string))

        time_a = datetime.strptime('2019-12-01 13:50:50,425', '%Y-%m-%d %H:%M:%S,%f')
        time_b = datetime.strptime('2019-12-31 13:50:52,663', '%Y-%m-%d %H:%M:%S,%f')
        self.assertFalse(match_error_string(file_path, time_a, time_b, match_string))

    def _read_healthcheck_cache_file(name):
        """Auxiliary function to read files from ./data used by the tests"""

        file_path = './data/' + name
        with open(file_path, 'r') as f:
            return f.read()

    @patch('builtins.open', mock_open(read_data=_read_healthcheck_cache_file('healthcheck_cache_valid.json')))
    def test_read_cache_file(self):
        """Test read_cache_file with valid file"""

        a, b = read_cache_file()
        self.assertFalse(a)
        self.assertEqual(b, datetime.strptime('2019-11-27 17:27:08,602172', '%Y-%m-%d %H:%M:%S,%f'))

    @patch('builtins.open', mock_open(read_data=_read_healthcheck_cache_file('healthcheck_cache_wrong_key.json')))
    def test_read_invalid_cache_file(self):
        """Test read_cache_file with a file with one wrong key"""

        a, b = read_cache_file()
        self.assertTrue(a)
        self.assertIsNone(b)

    @patch('builtins.open', mock_open(read_data=_read_healthcheck_cache_file('healthcheck_cache_invalid.json')))
    def test_read_invalid_json_cache_file(self):
        """Test read_cache_file with an invalid JSON file"""

        a, b = read_cache_file()
        self.assertTrue(a)
        self.assertIsNone(b)


if __name__ == "__main__":
    unittest.main(warnings='ignore')
