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
#     Alvaro del Castillo <acs@bitergia.com>
#

import copy
import json
import logging
import operator
import requests
import yaml

import panels

from utils.pythagoras import upload
from sirmordred.task import Task

logger = logging.getLogger(__name__)


def get_sigils_path():
    sigils_path = panels.__file__.replace('panels/__init__.py', '')
    return sigils_path


class TaskPanels(Task):
    """
    Upload all the Kibana dashboards/GrimoireLab panels based on the menu file.
    Furthermore it also sets up the top menu information and Kibiter configurations
    (e.g., default index pattern and time picker).
    """
    def __init__(self, conf):
        super().__init__(conf)

    def execute(self):
        # Configure kibiter

        overwrite_dashboards = not self.conf['panels']["strict"]
        dashboards_path = get_sigils_path() + 'json'
        kibiter_time_from = self.conf['panels']['kibiter_time_from']
        kibiter_default_index = self.conf['panels']['kibiter_default_index']
        kibiter_url = self.conf['panels']['kibiter_url']
        kibiter_index = self.conf['panels']['kibiter_index']
        kibiter_version = self.conf['panels']['kibiter_version']
        import_dashboards = self.conf['panels']['import_panels']
        set_top_menu = self.conf['panels']['set_top_menu']
        set_project_name = self.conf['panels']['set_project_name']
        elasticsearch_url = self.conf['es_enrichment']['url']
        menu_path = self.conf['general']['menu_file']

        logger.info("Pythagoras is starting...")
        upload(kibiter_url, kibiter_index, elasticsearch_url, dashboards_path, menu_path,
               import_dashboards, overwrite_dashboards, set_top_menu, set_project_name)
        logger.info("Pythagoras has finished!")
