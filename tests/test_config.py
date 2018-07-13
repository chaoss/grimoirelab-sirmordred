#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 Bitergia
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
#     Valerio Cosentino <valcos@bitergia.com>

import sys
import tempfile
import unittest

# Hack to make sure that tests import the right packages
# due to setuptools behaviour
sys.path.insert(0, '..')

from sirmordred.config import (Config, logger)

CONF_FULL = 'test.cfg'
CONF_SLIM = 'test_studies.cfg'
CONF_WRONG = 'test_wrong.cfg'


class TestConfig(unittest.TestCase):
    """Config tests"""

    def test_init(self):
        """Test whether attributes are initializated"""

        config = Config(CONF_FULL)

        self.assertIsNotNone(config.conf)
        self.assertIsNone(config.raw_conf)
        self.assertEqual(config.conf_list, [CONF_FULL])
        self.assertEqual(len(config.conf.keys()), 42)

    def test_init_studies(self):
        """Test whether studies' attributes are initializated"""

        config = Config(CONF_SLIM)

        self.assertIsNotNone(config.conf)
        self.assertIsNone(config.raw_conf)
        self.assertEqual(config.conf_list, [CONF_SLIM])
        self.assertEqual(len(config.conf.keys()), 14)

        self.assertTrue('general' in config.conf.keys())
        self.assertTrue('projects' in config.conf.keys())
        self.assertTrue('es_collection' in config.conf.keys())
        self.assertTrue('es_enrichment' in config.conf.keys())
        self.assertTrue('sortinghat' in config.conf.keys())
        self.assertTrue('panels' in config.conf.keys())
        self.assertTrue('phases' in config.conf.keys())

        self.assertTrue('git' in config.conf.keys())
        self.assertTrue('enrich_demography:git' in config.conf.keys())
        self.assertTrue('no_incremental' in config.conf['enrich_demography:git'].keys())

        self.assertTrue('enrich_areas_of_code:git' in config.conf.keys())
        self.assertTrue('in_index' in config.conf['enrich_areas_of_code:git'].keys())
        self.assertTrue('out_index' in config.conf['enrich_areas_of_code:git'].keys())
        self.assertTrue('sort_on_field' in config.conf['enrich_areas_of_code:git'].keys())
        self.assertTrue('no_incremental' in config.conf['enrich_areas_of_code:git'].keys())

        self.assertTrue('enrich_onion:git' in config.conf.keys())
        self.assertTrue('in_index' in config.conf['enrich_onion:git'].keys())
        self.assertTrue('out_index' in config.conf['enrich_onion:git'].keys())
        self.assertTrue('data_source' in config.conf['enrich_onion:git'].keys())
        self.assertTrue('contribs_field' in config.conf['enrich_onion:git'].keys())
        self.assertTrue('timeframe_field' in config.conf['enrich_onion:git'].keys())
        self.assertTrue('sort_on_field' in config.conf['enrich_onion:git'].keys())
        self.assertTrue('no_incremental' in config.conf['enrich_onion:git'].keys())

        self.assertTrue('github:issues' in config.conf.keys())
        self.assertTrue('enrich_onion:github' in config.conf.keys())
        self.assertTrue('in_index_iss' in config.conf['enrich_onion:github'].keys())
        self.assertTrue('in_index_prs' in config.conf['enrich_onion:github'].keys())
        self.assertTrue('out_index_iss' in config.conf['enrich_onion:github'].keys())
        self.assertTrue('in_index_prs' in config.conf['enrich_onion:github'].keys())
        self.assertTrue('data_source_iss' in config.conf['enrich_onion:github'].keys())
        self.assertTrue('data_source_prs' in config.conf['enrich_onion:github'].keys())
        self.assertTrue('contribs_field' in config.conf['enrich_onion:github'].keys())
        self.assertTrue('timeframe_field' in config.conf['enrich_onion:github'].keys())
        self.assertTrue('sort_on_field' in config.conf['enrich_onion:github'].keys())
        self.assertTrue('no_incremental' in config.conf['enrich_onion:github'].keys())

        self.assertTrue('github:pulls' in config.conf.keys())

    def test_create_config_file(self):
        """Test whether a config file is correctly created"""

        tmp_path = tempfile.mktemp(prefix='mordred_')

        config = Config(CONF_FULL)
        config.create_config_file(tmp_path)
        copied_config = Config(tmp_path)
        # TODO create_config_file produces a config different from the original one
        # self.assertDictEqual(config.conf, copied_config.conf)

    def test_check_config(self):
        """Test whether the config is properly checked"""

        with self.assertRaises(Exception):
            Config(CONF_WRONG)

    def test_get_data_sources(self):
        """Test whether all data sources are properly retrieved"""

        config = Config(CONF_FULL)

        expected = ['askbot', 'bugzilla', 'bugzillarest', 'confluence', 'discourse', 'dockerhub', 'functest',
                    'gerrit', 'git', 'github', 'google_hits', 'hyperkitty', 'jenkins', 'jira', 'mbox', 'meetup',
                    'mediawiki', 'mozillaclub', 'nntp', 'phabricator', 'pipermail', 'redmine', 'remo', 'rss',
                    'stackexchange', 'slack', 'supybot', 'telegram', 'twitter']
        data_sources = config.get_data_sources()

        self.assertEqual(len(data_sources), len(expected))
        self.assertEqual(data_sources.sort(), expected.sort())

    def test_set_param(self):
        """Test whether a param is correctly modified"""

        config = Config(CONF_FULL)

        self.assertFalse(config.conf['twitter']['collect'])
        config.set_param("twitter", "collect", "true")
        self.assertTrue(config.conf['twitter']['collect'])

    def test_set_param_not_found(self):
        """Test whether an error is logged if a param does not exist"""

        config = Config(CONF_FULL)

        with self.assertLogs(logger, level='ERROR') as cm:
            config.set_param("twitter", "acme", "true")
            self.assertEqual(cm.output[-1], 'ERROR:sirmordred.config:Config section twitter and param acme not exists')


if __name__ == "__main__":
    # logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')
    unittest.main(warnings='ignore')
