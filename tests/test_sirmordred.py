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
#     Valerio Cosentino <valcos@bitergia.com>


import sys
import unittest

# Hack to make sure that tests import the right packages
# due to setuptools behaviour
sys.path.insert(0, '..')

from sirmordred.config import Config
from sirmordred.sirmordred import logger, SirMordred

CONF_FILE = 'test.cfg'


class TestTaskRawDataCollection(unittest.TestCase):
    """Task tests"""

    def setUp(self):
        self.config = Config(CONF_FILE)
        self.sirmordred = SirMordred(self.config)

    def test_initialization(self):
        """Test whether attributes are initializated"""

        self.assertTrue(self.sirmordred.config, self.config)
        self.assertTrue(self.sirmordred.conf, self.config.get_conf())
        self.assertIsNotNone(self.sirmordred.grimoire_con)

    def test_check_es_access(self):
        """Test whether check_es_access properly works"""

        self.sirmordred = SirMordred(self.config)
        self.assertTrue(self.sirmordred.check_es_access())

    def test_check_es_access_es_collection_error(self):
        """Test whether an exception is thrown when es_collection is empty"""

        self.sirmordred = SirMordred(self.config)
        self.sirmordred.config.conf['es_collection']['url'] = ""
        with self.assertLogs(logger, level='ERROR') as cm:
            self.sirmordred.check_es_access()
            self.assertTrue(cm.output[-1], 'ERROR:sirmordred.sirmordred:Cannot connect to Elasticsearch: ')

    def test_check_es_access_es_es_enrichment_error(self):
        """Test whether an exception is thrown when es_enrichment is empty"""

        self.sirmordred = SirMordred(self.config)
        self.sirmordred.config.conf['es_enrichment']['url'] = ""
        with self.assertLogs(logger, level='ERROR') as cm:
            self.sirmordred.check_es_access()
            self.assertTrue(cm.output[-1], 'ERROR:sirmordred.sirmordred:Cannot connect to Elasticsearch: ')


if __name__ == "__main__":
    unittest.main(warnings='ignore')
