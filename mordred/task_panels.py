#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Bitergia
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
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# Authors:
#     Luis Cañas-Díaz <lcanas@bitergia.com>
#     Alvaro del Castillo <acs@bitergia.com>
#

import json
import logging
import requests
import yaml

from collections import OrderedDict
from urllib.parse import urljoin

from grimoire_elk.panels import import_dashboard, get_dashboard_name
from mordred.task import Task

logger = logging.getLogger(__name__)


class TaskPanels(Task):
    """ Create the panels  """

    panels_common = ["panels/dashboards5/overview.json",
                     "panels/dashboards5/about.json",
                     "panels/dashboards5/data-status.json"]

    # aliases not following the ds-raw and ds rule
    aliases = {
        "bugzillarest": {
            "raw":["bugzilla-raw"],
            "enrich":["bugzilla"]
        },
        "git": {
            "raw":["git-raw"],
            "enrich":["git", "git_author", "git_enrich"]
        },
        "github": {
            "raw":["github-raw"],
            "enrich":["github_issues", "github_issues_enrich", "issues_closed",
                      "issues_created", "issues_updated"]
        },
        "jenkins": {
            "raw":["jenkins-raw"],
            "enrich":["jenkins", "jenkins_enrich"]
        },
        "mbox": {
            "raw":["mbox-raw"],
            "enrich":["mbox", "mbox_enrich"]
        },
        "pipermail": {
            "raw":["pipermail-raw"],
            "enrich":["mbox", "mbox_enrich"]
        },
        "phabricator": {
            "raw":["phabricator-raw"],
            "enrich":["phabricator", "maniphest"]
        },
        "remo": {
            "raw":["remo-raw"],
            "enrich":["remo", "remo2-events"]
        },
        "stackexchange": {
            "raw":["stackexchange-raw"],
            "enrich":["stackoverflow"]
        },
        "supybot": {
            "raw":["irc-raw"],
            "enrich":["irc"]
        }
    }

    def __init__(self, conf):
        super().__init__(conf)
        # Read panels and menu description from yaml file """
        with open(TaskPanelsMenu.MENU_YAML, 'r') as f:
            try:
                self.panels_menu = yaml.load(f)
            except yaml.YAMLError as ex:
                logger.error(ex)
                raise
        # Panels are extracted from the global menu file
        self.panels = {}
        for ds in self.panels_menu:
            if ds['source'] not in self.panels:
                self.panels[ds['source']] = []
            for entry in ds['menu']:
                self.panels[ds['source']].append(entry['panel'])

    def __remove_alias(self, es_url, alias):
        alias_url = urljoin(es_url+"/", "_alias/"+alias)
        r = requests.get(alias_url)
        if r.status_code == 200:
            # The alias exists, let's remove it
            real_index = list(r.json())[0]
            logger.debug("Removing alias %s to %s", alias, real_index)
            aliases_url = urljoin(es_url+"/", "_aliases")
            action = """
            {
                "actions" : [
                    {"remove" : { "index" : "%s",
                                  "alias" : "%s" }}
               ]
             }
            """ % (real_index, alias)
            r = requests.post(aliases_url, data=action)
            r.raise_for_status()

    def __create_alias(self, es_url, es_index, alias):
        self.__remove_alias(es_url, alias)
        logger.debug("Adding alias %s to %s", alias, es_index)
        alias_url = urljoin(es_url+"/", "_aliases")
        action = """
        {
            "actions" : [
                {"add" : { "index" : "%s",
                           "alias" : "%s" }}
           ]
         }
        """ % (es_index, alias)

        logger.debug("%s %s", alias_url, action)
        r = requests.post(alias_url, data=action)
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError:
            logger.error("Can't create in %s %s", alias_url, action)
            raise

    def __create_aliases(self):
        """ Create aliases in ElasticSearch used by the panels """
        real_alias = self.backend_section.replace(":","_")  # remo:activities -> remo_activities
        es_col_url = self._get_collection_url()
        es_enrich_url = self.conf['es_enrichment']['url']

        index_raw = self.conf[self.backend_section]['raw_index']
        index_enrich = self.conf[self.backend_section]['enriched_index']

        if self.backend_section in self.aliases and \
            'raw' in self.aliases[self.backend_section]:
            for alias in self.aliases[self.backend_section]['raw']:
                self.__create_alias(es_col_url, index_raw, alias)
        else:
            # Standard alias for the raw index
            self.__create_alias(es_col_url, index_raw, real_alias + "-raw")

        if self.backend_section in self.aliases and \
            'enrich' in self.aliases[self.backend_section]:
            for alias in self.aliases[self.backend_section]['enrich']:
                self.__create_alias(es_enrich_url, index_enrich, alias)
        else:
            # Standard alias for the enrich index
            self.__create_alias(es_enrich_url, index_enrich, real_alias)


    def execute(self):
        # Create the aliases
        self.__create_aliases()
        # Create the commons panels
        # TODO: do it only one time, not for every backend
        for panel_file in self.panels_common:
            import_dashboard(self.conf['es_enrichment']['url'], panel_file)
        # Create the panels which uses the aliases as data source
        if self.backend_section in self.panels:
            for panel_file in self.panels[self.get_backend(self.backend_section)]:
                import_dashboard(self.conf['es_enrichment']['url'], panel_file)
        else:
            logger.warning("No panels found for %s", self.backend_section)


class TaskPanelsMenu(Task):
    """ Create the menu to access the panels  """

    MENU_YAML = 'menu.yaml'

    menu_panels_common = {
        "Overview": "Overview",
        "About": "About",
        "Data Status": "Data-Status"
    }

    def __init__(self, conf):
        super().__init__(conf)
        # Read panels and menu description from yaml file """
        with open(self.MENU_YAML, 'r') as f:
            try:
                self.panels_menu = yaml.load(f)
            except yaml.YAMLError as ex:
                logger.error(ex)
                raise
        # Get the active data sources
        self.data_sources = self.__get_active_data_sources()

    def is_backend_task(self):
        return False

    def __get_active_data_sources(self):
        active_ds = []
        for entry in self.panels_menu:
            ds = entry['source']
            if ds in self.conf.keys():
                active_ds.append(ds)
        logger.debug("Active data sources for menu: %s", active_ds)
        return active_ds

    def __create_dashboard_menu(self, dash_menu):
        """ Create the menu definition to access the panels in a dashboard """
        logger.info("Adding dashboard menu definition")
        menu_url = urljoin(self.conf['es_enrichment']['url'] + "/", ".kibana/metadashboard/main")
        # r = requests.post(menu_url, data=json.dumps(dash_menu, sort_keys=True))
        r = requests.post(menu_url, data=json.dumps(dash_menu))
        r.raise_for_status()

    def __remove_dashboard_menu(self):
        """ The dashboard must be removed before creating a new one """
        logger.info("Remove dashboard menu definition")
        menu_url = urljoin(self.conf['es_enrichment']['url'] + "/" , ".kibana/metadashboard/main")
        requests.delete(menu_url)

    def __get_menu_entries(self):
        """ Get the menu entries from the panel definition """
        menu_entries = OrderedDict()
        for entry in self.panels_menu:
            if entry['source'] not in self.data_sources:
                continue
            if 'kibana' in self.conf and self.conf['general']['kibana'] == '5':
                menu_entries[entry['name']] = {}
            for subentry in entry['menu']:
                dash_name = get_dashboard_name(subentry['panel'])
                # The name for the entry is in self.panels_menu
                if 'kibana' in self.conf and self.conf['general']['kibana'] == '5':
                    menu_entries[entry['name']][subentry['name']] = dash_name
                else:
                    menu_entries[dash_name] = dash_name

        return menu_entries

    def __get_dash_menu(self):
        """ Order the dashboard menu """
        # We need to get the current entries and add the new one
        current_menu = {}

        omenu = OrderedDict()
        if 'kibana' in self.conf and self.conf['general']['kibana'] == '5':
            # Kibana5 menu version
            omenu["Overview"] = self.menu_panels_common['Overview']
            ds_menu = self.__get_menu_entries()
            omenu.update(ds_menu)
            omenu["Data Status"] = self.menu_panels_common['Data Status']
            omenu["About"] = self.menu_panels_common['About']
        else:
            # First the Overview
            omenu["Overview"] = self.menu_panels_common['Overview']
            ds_menu = self.__get_menu_entries()
            for entry in ds_menu:
                name = entry.replace("-", " ")
                omenu[name] = ds_menu[entry]
            omenu.update(current_menu)
            # At the end Data Status, About
            omenu["Data Status"] = self.menu_panels_common['Data Status']
            omenu["About"] = self.menu_panels_common['About']

        logger.debug("Menu for panels: %s", json.dumps(ds_menu, indent=4))

        return omenu

    def execute(self):
        # Create the panels menu
        menu = self.__get_dash_menu()
        # Remove the current menu and create the new one
        self.__remove_dashboard_menu()
        self.__create_dashboard_menu(menu)
