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

from kidash.kidash import import_dashboard, get_dashboard_name, \
    exists_dashboard
from mordred.task import Task

logger = logging.getLogger(__name__)

# Header mandatory in Ellasticsearc 6 (optional in earlier versions)
ES6_HEADER = {"Content-Type": "application/json"}
ES6_KIBANA_INIT_DATA = '{"value": "*"}'
ES6_KIBANA_INIT_URL_PATH = "/api/kibana/settings/indexPattern:placeholder"


def es_version(url):
    """Get Elasticsearch version.

    Get the version of Elasticsearch. This is useful because
    Elasticsearch and Kibiter are paired (same major version for 5, 6).

    :param url: Elasticseearch url hosting Kibiter indices
    :returns:   major version, as string
    """

    res = requests.get(url)
    res.raise_for_status()
    major = res.json()['version']['number'].split(".")[0]
    return major


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

        # FIXME exceptions raised here are not handled!!

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

    def __kibiter_version(self, major):
        """ Get the kibiter vesion.

        :param major: major Elasticsearch version
        """
        version = None

        es_url = self.conf['es_enrichment']['url']
        if major == "6":
            config_url = '.kibana/_search'
            url = urljoin(es_url + "/", config_url)
            query = {
                "stored_fields": ["_id"],
                "query": {
                    "term": {
                        "type": "config"
                    }
                }
            }
            try:
                res = self.grimoire_con.get(url, data=json.dumps(query), headers=ES6_HEADER)
                res.raise_for_status()
                version = res.json()['hits']['hits'][0]['_id'].split(':', 1)[1]
            except Exception:
                logger.error("Can not find kibiter version")
        else:
            config_url = '.kibana/config/_search'
            url = urljoin(es_url + "/", config_url)
            res = self.grimoire_con.get(url)
            res.raise_for_status()
            version = res.json()['hits']['hits'][0]['_id']
        logger.debug("Kibiter version: %s", version)
        return version

    def __kb6_update_config(self, url, data):
        """Update config in Kibana6.

        Up to Kibana 6, you just updated properties in a dictionary,
        but now the whole config data is a dictionary itself: we
        need to read it, update the dictionary, and upload it again.

        :param url: url to read and update
        :param data: data to update
        """

        query = {
            "query": {
                "term": {
                    "type": "config"
                }
            }
        }
        res = self.grimoire_con.get(url, data=json.dumps(query),
                                    headers=ES6_HEADER)
        res.raise_for_status()
        item = res.json()['_source']
        for field, value in data.items():
            item['config'][field] = value
        res = self.grimoire_con.post(url, data=json.dumps(item),
                                     headers=ES6_HEADER)
        res.raise_for_status()

    def __configure_kibiter(self):

        if 'panels' not in self.conf:
            logger.warning("Panels config not availble. Not configuring Kibiter.")
            return False

        kibiter_major = es_version(self.conf['es_enrichment']['url'])
        if kibiter_major == "6":
            if self.conf['panels']["kibiter_url"] and self.conf['panels']["kibiter_version"]:
                # Force the creation of the .kibana index
                # We don't have this data so it just works for this value
                k6_init_url = self.conf['panels']["kibiter_url"]
                k6_init_url += ES6_KIBANA_INIT_URL_PATH
                k6_init_headers = {
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "kbn-version": self.conf['panels']['kibiter_version']
                }

                try:
                    res = self.grimoire_con.post(k6_init_url, headers=k6_init_headers,
                                                 data=ES6_KIBANA_INIT_DATA)
                    res.raise_for_status()
                except Exception as ex:
                    logger.error("Can not create the .kibana in ES6 %s", ex)

        kibiter_time_from = self.conf['panels']['kibiter_time_from']
        kibiter_default_index = self.conf['panels']['kibiter_default_index']

        logger.info("Configuring Kibiter %s for default index %s and time frame %s",
                    kibiter_major, kibiter_default_index, kibiter_time_from)

        kibiter_version = self.__kibiter_version(kibiter_major)
        if not kibiter_version:
            return False
        print("Kibiter/Kibana: version found is %s" % kibiter_version)
        time_picker = "{\n  \"from\": \"" + kibiter_time_from \
            + "\",\n  \"to\": \"now\",\n  \"mode\": \"quick\"\n}"

        if kibiter_major == "6":
            config_resource = '.kibana/doc/config:' + kibiter_version
        else:
            config_resource = '.kibana/config/' + kibiter_version
        kibiter_config = {
            "defaultIndex": kibiter_default_index,
            "timepicker:timeDefaults": time_picker
        }

        es_url = self.conf['es_enrichment']['url']
        url = urljoin(es_url + "/", config_resource)
        if kibiter_major == "6":
            self.__kb6_update_config(url, data=kibiter_config)
        else:
            res = self.grimoire_con.post(url, data=json.dumps(kibiter_config),
                                         headers=ES6_HEADER)
            res.raise_for_status()

        return True

    def __create_dashboard(self, panel_file, data_sources=None):
        """Upload a panel to Elasticsearch if it does not exist yet.

        If a list of data sources is specified, upload only those
        elements (visualizations, searches) that match that data source.

        :param panel_file: file name of panel (dashobard) to upload
        :param data_sources: list of data sources
        """
        es_enrich = self.conf['es_enrichment']['url']
        # If the panel (dashboard) already exists, don't load it
        dash_id = get_dashboard_name(panel_file)
        if exists_dashboard(es_enrich, dash_id):
            logger.info("Not creating a panel that exists already: %s", dash_id)
        else:
            logger.info("Creating the panel: %s", dash_id)
            if data_sources and 'pipermail' in data_sources:
                # the dashboard for mbox and pipermail are the same
                data_sources = list(data_sources)
                data_sources.append('mbox')
            import_dashboard(es_enrich, panel_file, data_sources=data_sources)

    def execute(self):
        # Configure kibiter
        if self.__configure_kibiter():
            print("Kibiter/Kibana: configured!")
        else:
            logger.error("Can not configure kibiter")

        print("Panels, visualizations: uploading...")
        # Create the commons panels
        for panel_file in self.panels_common:
            self.__create_dashboard(panel_file, data_sources=self.panels.keys())

        # Upload all the Kibana dashboards/GrimoireLab panels based on
        # enabled data sources AND the menu file
        for ds in self.panels:
            for panel_file in self.panels[ds]:
                try:
                    self.__create_dashboard(panel_file)
                except Exception as ex:
                    logger.error("%s not correctly uploaded (%s)", panel_file, ex)
        print("Panels, visualziations: uploaded!")


class TaskPanelsAliases(Task):
    """ Create the aliases needed for the panels """

    # aliases not following the ds-raw and ds rule
    aliases = {
        "apache": {
            "raw": ["apache"]
        },
        "bugzillarest": {
            "raw": ["bugzilla-raw"],
            "enrich": ["bugzilla"]
        },
        "dockerhub": {
            "raw": ["dockerhub-raw"],
            "enrich": ["dockerhub"]
        },
        "functest": {
            "raw": ["functest-raw"],
            "enrich": ["functest"]
        },
        "git": {
            "raw": ["git-raw"],
            "enrich": ["git", "git_author", "git_enrich"]
        },
        "github": {
            "raw": ["github-raw"],
            "enrich": ["github_issues", "github_issues_enrich", "issues_closed",
                       "issues_created", "issues_updated"]
        },
        "google_hits": {
            "raw": ["google-hits"]
        },
        "jenkins": {
            "raw": ["jenkins-raw"],
            "enrich": ["jenkins", "jenkins_enrich"]
        },
        "mbox": {
            "raw": ["mbox-raw"],
            "enrich": ["mbox", "mbox_enrich"]
        },
        "pipermail": {
            "raw": ["pipermail-raw"],
            "enrich": ["mbox", "mbox_enrich"]
        },
        "phabricator": {
            "raw": ["phabricator-raw"],
            "enrich": ["phabricator", "maniphest"]
        },
        "remo": {
            "raw": ["remo-raw"],
            "enrich": ["remo", "remo-events", "remo2-events", "remo-events_metadata__timestamp"]
        },
        "remo:activities": {
            "raw": ["remo_activities-raw"],
            "enrich": ["remo-activities", "remo2-activities", "remo-activities_metadata__timestamp"]
        },
        "stackexchange": {
            "raw": ["stackexchange-raw"],
            "enrich": ["stackoverflow"]
        },
        "supybot": {
            "raw": ["irc-raw"],
            "enrich": ["irc"]
        }
    }

    def __exists_alias(self, es_url, alias):
        exists = False

        alias_url = urljoin(es_url + "/", "_alias/" + alias)
        res = self.grimoire_con.get(alias_url)
        if res.status_code == 200:
            # The alias exists
            exists = True
        return exists

    def __remove_alias(self, es_url, alias):
        alias_url = urljoin(es_url + "/", "_alias/" + alias)
        res = self.grimoire_con.get(alias_url)
        if res.status_code == 200:
            real_index = list(res.json())[0]
            logger.debug("Removing alias %s to %s", alias, real_index)
            aliases_url = urljoin(es_url + "/", "_aliases")
            action = """
            {
                "actions" : [
                    {"remove" : { "index" : "%s",
                                  "alias" : "%s" }}
               ]
             }
            """ % (real_index, alias)
            res = self.grimoire_con.post(aliases_url, data=action, headers=ES6_HEADER)
            res.raise_for_status()

    def __create_alias(self, es_url, es_index, alias):
        if self.__exists_alias(es_url, alias):
            # The alias already exists
            return
        logger.debug("Adding alias %s to %s", alias, es_index)
        alias_url = urljoin(es_url + "/", "_aliases")
        action = """
        {
            "actions" : [
                {"add" : { "index" : "%s",
                           "alias" : "%s" }}
           ]
         }
        """ % (es_index, alias)

        logger.debug("%s %s", alias_url, action)
        res = self.grimoire_con.post(alias_url, data=action, headers=ES6_HEADER)
        try:
            res.raise_for_status()
        except requests.exceptions.HTTPError:
            logger.warning("Can't create in %s %s", alias_url, action)
            if res.status_code == 404:
                # Enrich index not found
                logger.warning("The enriched index does not exists: %s", es_index)
            else:
                raise

    def __create_aliases(self):
        """ Create aliases in ElasticSearch used by the panels """
        real_alias = self.backend_section.replace(":", "_")  # remo:activities -> remo_activities
        es_col_url = self._get_collection_url()
        es_enrich_url = self.conf['es_enrichment']['url']

        index_raw = self.conf[self.backend_section]['raw_index']
        index_enrich = self.conf[self.backend_section]['enriched_index']

        if (self.backend_section in self.aliases and
            'raw' in self.aliases[self.backend_section]):
            for alias in self.aliases[self.backend_section]['raw']:
                self.__create_alias(es_col_url, index_raw, alias)
        else:
            # Standard alias for the raw index
            self.__create_alias(es_col_url, index_raw, real_alias + "-raw")

        if (self.backend_section in self.aliases and
            'enrich' in self.aliases[self.backend_section]):
            for alias in self.aliases[self.backend_section]['enrich']:
                self.__create_alias(es_enrich_url, index_enrich, alias)
        else:
            # Standard alias for the enrich index
            self.__create_alias(es_enrich_url, index_enrich, real_alias)

    def execute(self):
        # Create the aliases
        print("Elasticsearch aliases: creating...")
        self.__create_aliases()
        print("Elasticsearch aliases: created!")


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
        if 'shortname' in self.conf['general']:
            self.project_name = self.conf['general']['short_name']
        else:
            self.project_name = 'GrimoireLab'

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

    def __upload_title(self, kibiter_major):
        """Upload to Kibiter the title for the dashboard.

        The title is shown on top of the dashboard menu, and is Usually
        the name of the project being dashboarded.
        This is done only for Kibiter 6.x.

        :param kibiter_major: major version of kibiter
        """

        if kibiter_major == "6":
            resource = ".kibana/doc/projectname"
            data = {"projectname": {"name": self.project_name}}
            mapping_resource = ".kibana/_mapping/doc"
            mapping = {"dynamic": "true"}

            url = urljoin(self.conf['es_enrichment']['url'] + "/", resource)
            mapping_url = urljoin(self.conf['es_enrichment']['url'] + "/",
                                  mapping_resource)

            logger.debug("Adding mapping for dashboard title")
            res = self.grimoire_con.put(mapping_url, data=json.dumps(mapping),
                                        headers=ES6_HEADER)
            try:
                res.raise_for_status()
            except requests.exceptions.HTTPError:
                logger.error("Couldn't create mapping for dashboard title.")
                logger.error(res.json())

            logger.debug("Uploading dashboard title")
            res = self.grimoire_con.post(url, data=json.dumps(data),
                                         headers=ES6_HEADER)
            try:
                res.raise_for_status()
            except requests.exceptions.HTTPError:
                logger.error("Couldn't create dashboard title.")
                logger.error(res.json())

    def __create_dashboard_menu(self, dash_menu, kibiter_major):
        """ Create the menu definition to access the panels in a dashboard.

        :param          menu: dashboard menu to upload
        :param kibiter_major: major version of kibiter
        """
        logger.info("Adding dashboard menu")
        if kibiter_major == "6":
            menu_resource = ".kibana/doc/metadashboard"
            mapping_resource = ".kibana/_mapping/doc"
            mapping = {"dynamic": "true"}
            menu = {'metadashboard': dash_menu}
        else:
            menu_resource = ".kibana/metadashboard/main"
            mapping_resource = ".kibana/_mapping/metadashboard"
            mapping = {"dynamic": "true"}
            menu = dash_menu
        menu_url = urljoin(self.conf['es_enrichment']['url'] + "/",
                           menu_resource)
        # r = requests.post(menu_url, data=json.dumps(dash_menu, sort_keys=True))
        mapping_url = urljoin(self.conf['es_enrichment']['url'] + "/",
                              mapping_resource)
        logger.debug("Adding mapping for metadashbaord")
        res = self.grimoire_con.put(mapping_url, data=json.dumps(mapping),
                                    headers=ES6_HEADER)
        try:
            res.raise_for_status()
        except requests.exceptions.HTTPError:
            logger.error("Couldn't create mapping for Kibiter menu.")
        res = self.grimoire_con.post(menu_url, data=json.dumps(menu),
                                     headers=ES6_HEADER)
        try:
            res.raise_for_status()
        except requests.exceptions.HTTPError:
            logger.error("Couldn't create Kibiter menu.")
            logger.error(res.json())
            raise

    def __remove_dashboard_menu(self, kibiter_major):
        """ Remove existing menu for dashboard, if any.

        Usually, we remove the menu before creating a new one.

        :param kibiter_major: major version of kibiter
        """
        logger.info("Removing old dashboard menu, if any")
        if kibiter_major == "6":
            metadashboard = ".kibana/doc/metadashboard"
        else:
            metadashboard = ".kibana/metadashboard/main"
        menu_url = urljoin(self.conf['es_enrichment']['url'] + "/", metadashboard)
        self.grimoire_con.delete(menu_url)

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
        print("Kibiter/Kibana: uploading dashboard menu...")
        # Create the panels menu
        menu = self.__get_dash_menu()
        # Remove the current menu and create the new one
        kibiter_major = es_version(self.conf['es_enrichment']['url'])
        self.__upload_title(kibiter_major)
        self.__remove_dashboard_menu(kibiter_major)
        self.__create_dashboard_menu(menu, kibiter_major)
        print("Kibiter/Kibana: uploaded dashboard menu!")
