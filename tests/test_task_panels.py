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
#     Alvaro del Castillo <acs@bitergia.com>

import sys
import unittest

from unittest.mock import patch

# Hack to make sure that tests import the right packages
# due to setuptools behaviour
sys.path.insert(0, '..')

from sirmordred.config import Config
from sirmordred.task_panels import TaskPanels, TaskPanelsMenu

CONF_FILE = 'test.cfg'


def check_import_dashboard_stackexchange(elastic_url, import_file, es_index=None,
                                         data_sources=None, add_vis_studies=False, strict=False):
    """ Check that stackexchange data sources adds also stackoverflow
        data source which is the name used in panels """
    if "stackexchange" in data_sources and "stackoverflow" not in data_sources:
        raise RuntimeError('stackexchange present but stackoverflow no in data sources')


def check_create_dashboard(panel_file, data_sources):
    # data_sources must be only defined for Overview and Data Status panels
    if panel_file not in TaskPanels.panels_multi_ds and data_sources:
        raise RuntimeError('Creating %s with data sources filtering' % panel_file)
    if panel_file in TaskPanels.panels_multi_ds and not data_sources:
        raise RuntimeError('Creating %s without data sources filtering' % panel_file)


class TestTaskPanels(unittest.TestCase):
    """TaskPanels tests"""

    def test_initialization(self):
        """Test whether attributes are initializated"""

        config = Config(CONF_FILE)
        task = TaskPanels(config)

        self.assertEqual(task.config, config)

    @patch('sirmordred.task_panels.import_dashboard', side_effect=check_import_dashboard_stackexchange)
    @patch('sirmordred.task_panels.get_dashboard_name')
    def test_create_dashboard_stackexchange(self, mock_get_dashboard_name, mock_import_dashboard):
        """ Test the creation of a dashboard which includes stackexchange in data sources """
        mock_get_dashboard_name.return_value = ''

        config = Config(CONF_FILE)
        task = TaskPanels(config)

        task.create_dashboard(None, data_sources=["stackexchange"])

    @patch('sirmordred.task_panels.TaskPanels.create_dashboard', side_effect=check_create_dashboard)
    def test_create_dashboard_multi_ds(self, mock_get_dashboard_name):
        """ Test the creation of dashboards with filtered data sources """
        mock_get_dashboard_name.return_value = ''

        config = Config(CONF_FILE)
        task = TaskPanels(config)

        task.execute()


class TestTaskPanelsMenu(unittest.TestCase):
    """TaskPanelsMenu tests"""

    def test_initialization(self):
        """Test whether attributes are initializated"""

        config = Config(CONF_FILE)
        task = TaskPanelsMenu(config)

        self.assertEqual(task.config, config)

        self.assertEqual(len(task.panels_menu), 31)

        for entry in task.panels_menu:
            self.assertGreaterEqual(len(entry['index-patterns']), 0)


if __name__ == "__main__":
    # logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')
    unittest.main(warnings='ignore')
