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

from grimoire_elk.panels import import_dashboard, get_dashboard_name, exists_dashboard
from mordred.task import Task

logger = logging.getLogger(__name__)


class TaskPanels(Task):
    """ Upload all the Kibana dashboards/GrimoireLab panels based on
    enabled data sources AND the menu file. Before uploading the panels
    it also sets up common configuration variables for Kibiter
    """
    panels_common = ["panels/json/overview.json",
                     "panels/json/last_month_contributors.json",
                     "panels/json/about.json",
                     "panels/json/affiliations.json",
                     "panels/json/data_status.json"]

    def __init__(self, conf):
        super().__init__(conf)
        # Read panels and menu description from yaml file """
        with open(TaskPanelsMenu.MENU_YAML, 'r') as f:
            try:
                self.panels_menu = yaml.load(f)
            except yaml.YAMLError as ex:
                logger.error(ex)
                raise

        #FIXME exceptions raised here are not handled!!

        # Gets the cross set of enabled data sources and data sources
        # available in the menu file. For the result set gets the file
        # names to be uploaded
        enabled_ds = conf.get_data_sources()
        self.panels = {}

        for ds in self.panels_menu:
            if ds['source'] not in enabled_ds:
                continue
            for entry in ds['menu']:
                if ds['source'] not in self.panels.keys():
                    self.panels[ds['source']] = []
                self.panels[ds['source']].append(entry['panel'])

    def is_backend_task(self):
        return False

    def __kibiter_version(self):
        """ Get the kibiter vesion """
        config_url = '.kibana/config/_search'
        es_url = self.conf['es_enrichment']['url']
        url = urljoin(es_url + "/", config_url)
        r = requests.get(url)
        r.raise_for_status()
        return r.json()['hits']['hits'][0]['_id']

    def __configure_kibiter(self):
        if 'panels' not in self.conf:
            logger.warning("Panels config not availble. Not configuring Kibiter.")
            return

        kibiter_version = self.__kibiter_version()
        kibiter_time_from = self.conf['panels']['kibiter_time_from']
        kibiter_default_index = self.conf['panels']['kibiter_default_index']

        logger.info("Configuring Kibiter %s for default index %s and time frame %s",
                    kibiter_version, kibiter_default_index, kibiter_time_from)

        config_url = '.kibana/config/' + kibiter_version
        kibiter_config = {
            "defaultIndex": kibiter_default_index,
            "timepicker:timeDefaults":
                "{\n  \"from\": \""+ kibiter_time_from + "\",\n  \"to\": \"now\",\n  \"mode\": \"quick\"\n}"
        }

        es_url = self.conf['es_enrichment']['url']
        url = urljoin(es_url + "/", config_url)
        r = requests.post(url, data=json.dumps(kibiter_config))
        r.raise_for_status()

    def __create_dashboard(self, panel_file):
        es_enrich = self.conf['es_enrichment']['url']
        # If the panel (dashboard) already exists, don't load it
        dash_id = get_dashboard_name(panel_file)
        if exists_dashboard(es_enrich, dash_id):
            logger.info("Not creating a panel that exists already: %s", dash_id)
        else:
            logger.info("Creating the panel: %s", dash_id)
            import_dashboard(es_enrich, panel_file)

    def execute(self):
        # Configure kibiter
        self.__configure_kibiter()

        # Create the commons panels
        for panel_file in self.panels_common:
            self.__create_dashboard(panel_file)

        # Upload all the Kibana dashboards/GrimoireLab panels based on
        # enabled data sources AND the menu file
        for ds in self.panels:
            for panel_file in self.panels[ds]:
                try:
                    self.__create_dashboard(panel_file)
                except Exception as ex:
                    logger.error("%s not correctly uploaded (%s)", panel_file, ex)

class TaskPanelsAliases(Task):
    """ Create the aliases needed for the panels """

    # aliases not following the ds-raw and ds rule
    aliases = {
        "apache": {
            "raw":["apache"]
        },
        "bugzillarest": {
            "raw":["bugzilla-raw"],
            "enrich":["bugzilla"]
        },
        "dockerhub": {
            "raw":["dockerhub-raw"],
            "enrich":["dockerhub"]
        },
        "functest": {
            "raw":["functest-raw"],
            "enrich":["functest"]
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
        "google_hits": {
            "raw":["google-hits"]
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
            "enrich":["remo", "remo-events", "remo2-events", "remo-events_metadata__timestamp"]
        },
        "remo:activities": {
            "raw":["remo_activities-raw"],
            "enrich":["remo-activities", "remo2-activities", "remo-activities_metadata__timestamp"]
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

    def __exists_alias(self, es_url, alias):
        exists = False

        alias_url = urljoin(es_url+"/", "_alias/"+alias)
        r = requests.get(alias_url)
        if r.status_code == 200:
            # The alias exists
            exists = True
        return exists

    def __remove_alias(self, es_url, alias):
        alias_url = urljoin(es_url+"/", "_alias/"+alias)
        r = requests.get(alias_url)
        if r.status_code == 200:
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
        if self.__exists_alias(es_url, alias):
            # The alias already exists
            return
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
            logger.warning("Can't create in %s %s", alias_url, action)
            if r.status_code == 404:
                # Enrich index not found
                logger.warning("The enriched index does not exists: %s", es_index)
            else:
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
        metadashboard_mapping_url = urljoin(self.conf['es_enrichment']['url'] + "/",
                                            ".kibana/_mapping/metadashboard")
        r = requests.put(metadashboard_mapping_url, data=json.dumps({"dynamic": "true"}))
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError:
            logger.error("Cannot create mapping for Kibiter menu.")
        r = requests.post(menu_url, data=json.dumps(dash_menu))
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError:
            logger.error("Cannot create Kibiter menu. Probably it already exists for a different kibiter version.")
            raise

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
            if self.conf['general']['kibana'] == '5':
                menu_entries[entry['name']] = {}
            for subentry in entry['menu']:
                try:
                    dash_name = get_dashboard_name(subentry['panel'])
                except FileNotFoundError:
                    logging.error("Can't open dashboard file %s", subentry['panel'])
                    continue
                # The name for the entry is in self.panels_menu
                if self.conf['general']['kibana'] == '5':
                    menu_entries[entry['name']][subentry['name']] = dash_name
                else:
                    menu_entries[dash_name] = dash_name

        return menu_entries

    def __get_dash_menu(self):
        """ Order the dashboard menu """
        # We need to get the current entries and add the new one
        current_menu = {}

        omenu = OrderedDict()
        if self.conf['general']['kibana'] == '5':
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
