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
import unittest.mock

import httpretty
from urllib.parse import urljoin

# Hack to make sure that tests import the right packages
# due to setuptools behaviour
sys.path.insert(0, '..')

from sirmordred.config import Config
from sirmordred.task_panels import (KIBANA_SETTINGS_URL,
                                    TaskPanels,
                                    TaskPanelsMenu)

CONF_FILE = 'test.cfg'


class MockedTaskPanels(TaskPanels):
    VERSION = "5.6.0"

    def __init__(self, conf):
        super().__init__(conf)

    def es_version(self, url):
        return MockedTaskPanels.VERSION.split(".")[0]

    def create_dashboard(self, panel_file, data_sources=None, strict=True):
        return


def check_import_dashboard_stackexchange(elastic_url, import_file, es_index=None,
                                         data_sources=None, add_vis_studies=False, strict=False):
    """ Check that stackexchange data sources adds also stackoverflow
        data source which is the name used in panels """
    if "stackexchange" in data_sources and "stackoverflow" not in data_sources:
        raise RuntimeError('stackexchange present but stackoverflow no in data sources')


class TestTaskPanels(unittest.TestCase):
    """TaskPanels tests"""

    def test_initialization(self):
        """Test whether attributes are initializated"""

        config = Config(CONF_FILE)
        task = TaskPanels(config)

        self.assertEqual(task.config, config)

    @unittest.mock.patch('sirmordred.task_panels.import_dashboard', side_effect=check_import_dashboard_stackexchange)
    @unittest.mock.patch('sirmordred.task_panels.get_dashboard_name')
    def test_create_dashboard_stackexchange(self, mock_get_dashboard_name, mock_import_dashboard):
        """ Test the creation of a dashboard which includes stackexchange in data sources """
        mock_get_dashboard_name.return_value = ''

        config = Config(CONF_FILE)
        task = TaskPanels(config)

        panel_file = 'panels/json/stackoverflow.json'
        task.create_dashboard(panel_file, data_sources=["stackexchange"])

    def test_create_dashboard_multi_ds_kibiter_6(self):
        """ Test the creation of dashboards with filtered data sources """

        config = Config(CONF_FILE)
        es_url = config.conf['es_enrichment']['url']
        es_kibana_url = urljoin(es_url + "/", '.kibana')
        kibiter_api_url = urljoin(config.conf['panels']['kibiter_url'], KIBANA_SETTINGS_URL)
        kibiter_defaultIndex_url = kibiter_api_url + '/defaultIndex'
        kibiter_timePicker_url = kibiter_api_url + '/timepicker:timeDefaults'

        headers = {
            "Content-Type": "application/json",
            "kbn-xsrf": "true"
        }

        httpretty.register_uri(httpretty.GET,
                               es_kibana_url,
                               body={},
                               status=200)

        httpretty.register_uri(httpretty.POST,
                               kibiter_defaultIndex_url,
                               body={},
                               status=200,
                               forcing_headers=headers)

        httpretty.register_uri(httpretty.POST,
                               kibiter_timePicker_url,
                               body={},
                               status=200,
                               forcing_headers=headers)

        MockedTaskPanels.VERSION = '6.1.0'
        task = MockedTaskPanels(config)
        httpretty.enable(allow_net_connect=True)
        task.execute()
        httpretty.disable()

    def test_create_dashboard_multi_ds_kibiter_6_hhtp_error(self):
        """ Test the creation of dashboards with filtered data sources """

        config = Config(CONF_FILE)
        es_url = config.conf['es_enrichment']['url']
        es_kibana_url = urljoin(es_url + "/", '.kibana')
        kibiter_api_url = urljoin(config.conf['panels']['kibiter_url'], KIBANA_SETTINGS_URL)
        kibiter_defaultIndex_url = kibiter_api_url + '/defaultIndex'
        kibiter_timePicker_url = kibiter_api_url + '/timepicker:timeDefaults'

        headers = {
            "Content-Type": "application/json",
            "kbn-xsrf": "true"
        }

        httpretty.register_uri(httpretty.GET,
                               es_kibana_url,
                               body='{}',
                               status=200)

        httpretty.register_uri(httpretty.POST,
                               kibiter_defaultIndex_url,
                               body='{}',
                               status=200,
                               forcing_headers=headers)

        httpretty.register_uri(httpretty.POST,
                               kibiter_timePicker_url,
                               body='{}',
                               status=401,
                               forcing_headers=headers)

        MockedTaskPanels.VERSION = '6.1.0'
        task = MockedTaskPanels(config)
        httpretty.enable(allow_net_connect=True)
        task.execute()
        httpretty.disable()


class TestTaskPanelsMenu(unittest.TestCase):
    """TaskPanelsMenu tests"""

    def test_initialization(self):
        """Test whether attributes are initializated"""

        config = Config(CONF_FILE)
        task = TaskPanelsMenu(config)

        self.assertEqual(task.config, config)

        self.assertEqual(len(task.panels_menu), 34)

        for entry in task.panels_menu:
            self.assertGreaterEqual(len(entry['index-patterns']), 0)


if __name__ == "__main__":
    unittest.main(warnings='ignore')
