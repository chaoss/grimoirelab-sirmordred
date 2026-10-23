#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 Bitergia
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
#     Tanmay Baranwal <baranwaltanmay16@gmail.com>
#

import contextlib
import io
import sys
import unittest
from unittest import mock

# Hack to make sure that tests import the right packages
# due to setuptools behaviour
sys.path.insert(0, '..')

from sirmordred.utils.micro import get_params_parser


class TestGetParamsParser(unittest.TestCase):
    """micro.py command line parser tests"""

    def _print_help(self, option):
        """Parse `option` and return the exit code and the printed output"""

        # get_params_parser() prints the help and exits when called
        # without arguments, so give it a non-empty argv
        with mock.patch.object(sys, 'argv', ['micro.py', option]):
            parser = get_params_parser()

        output = io.StringIO()
        with contextlib.redirect_stdout(output), self.assertRaises(SystemExit) as exit_cm:
            parser.parse_args([option])

        return exit_cm.exception.code, output.getvalue()

    def test_help(self):
        """Test whether --help and -h print the options and exit successfully"""

        for option in ('--help', '-h'):
            with self.subTest(option=option):
                code, output = self._print_help(option)

                self.assertEqual(code, 0)
                self.assertIn('--raw', output)
                self.assertIn('--enrich', output)
                self.assertIn('--cfg', output)

    def test_help_hides_debug(self):
        """Test whether the hidden --debug option stays out of the help"""

        _, output = self._print_help('--help')

        self.assertNotIn('--debug', output)


if __name__ == '__main__':
    unittest.main()
