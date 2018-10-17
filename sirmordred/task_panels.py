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

import copy
import json
import logging
import requests
import yaml

from collections import OrderedDict
from urllib.parse import urljoin

from kidash.kidash import import_dashboard, get_dashboard_name, check_kibana_index
from sirmordred.task import Task

logger = logging.getLogger(__name__)

# Header mandatory in ElasticSearch 6
ES6_HEADER = {"Content-Type": "application/json"}
KIBANA_SETTINGS_URL = '/api/kibana/settings'

STRICT_LOADING = "strict"

KAFKA = "kafka"
KAFKA_PANEL = "panels/json/kip.json"
KAKFA_IP = "panels/json/kafka-index-pattern.json"

KAFKA_MENU = {
    'name': 'KIP',
    'source': KAFKA,
    'icon': 'default.png',
    'index-patterns': [KAKFA_IP],
    'menu': [
        {'name': 'Overview', 'panel': KAFKA_PANEL}
    ]
}

COMMUNITY = 'community'
ONION_PANEL_OVERALL = 'panels/json/onion_overall.json'
ONION_PANEL_PROJECTS = 'panels/json/onion_projects.json'
ONION_PANEL_ORGS = 'panels/json/onion_organizations.json'
DEMOGRAPHICS = 'panels/json/demographics.json'

ONION_PANEL_OVERALL_IP = 'panels/json/all_onion-index-pattern.json'
ONION_PANEL_PROJECTS_IP = 'panels/json/all_onion-index-pattern.json'
ONION_PANEL_ORGS_IP = 'panels/json/all_onion-index-pattern.json'
DEMOGRAPHICS_IP = 'panels/json/demographics-index-pattern.json'

COMMUNITY_MENU = {
    'name': 'Community',
    'source': COMMUNITY,
    'icon': 'default.png',
    'index-patterns': [
        ONION_PANEL_OVERALL_IP,
        ONION_PANEL_PROJECTS_IP,
        ONION_PANEL_ORGS_IP,
        DEMOGRAPHICS_IP
    ],
    'menu': [
        {'name': 'Overall', 'panel': ONION_PANEL_OVERALL},
        {'name': 'Projects', 'panel': ONION_PANEL_PROJECTS},
        {'name': 'Organizations', 'panel': ONION_PANEL_ORGS},
        {'name': 'Demographics', 'panel': DEMOGRAPHICS}
    ]
}

GITLAB_ISSUES = "gitlab-issues"
GITLAB_ISSUES_PANEL_OVERALL = "panels/json/gitlab_issues.json"
GITLAB_ISSUES_PANEL_BACKLOG = "panels/json/gitlab_issues_backlog.json"
GITLAB_ISSUES_PANEL_TIMING = "panels/json/gitlab_issues_timing.json"
GITLAB_ISSUES_IP = "panels/json/gitlab_issues-index-pattern.json"

GITLAB_ISSUES_MENU = {
    'name': 'GitLab Issues',
    'source': GITLAB_ISSUES,
    'icon': 'default.png',
    'index-patterns': [GITLAB_ISSUES_IP],
    'menu': [
        {'name': 'Overview', 'panel': GITLAB_ISSUES_PANEL_OVERALL},
        {'name': 'Backlog', 'panel': GITLAB_ISSUES_PANEL_BACKLOG},
        {'name': 'Timing', 'panel': GITLAB_ISSUES_PANEL_TIMING}
    ]
}

GITLAB_MERGES = "gitlab-merges"
GITLAB_MERGES_PANEL_OVERALL = "panels/json/gitlab_merge_requests.json"
GITLAB_MERGES_PANEL_BACKLOG = "panels/json/gitlab_merge_requests_backlog.json"
GITLAB_MERGES_PANEL_TIMING = "panels/json/gitlab_merge_requests_timing.json"
GITLAB_MERGES_IP = "panels/json/gitlab_merge_requests-index-pattern.json"

GITLAB_MERGES_MENU = {
    'name': 'GitLab Merges',
    'source': GITLAB_MERGES,
    'icon': 'default.png',
    'index-patterns': [GITLAB_MERGES_IP],
    'menu': [
        {'name': 'Overview', 'panel': GITLAB_MERGES_PANEL_OVERALL},
        {'name': 'Backlog', 'panel': GITLAB_MERGES_PANEL_BACKLOG},
        {'name': 'Timing', 'panel': GITLAB_MERGES_PANEL_TIMING}
    ]
}

MATTERMOST = "mattermost"
MATTERMOST_PANEL = "panels/json/mattermost.json"
MATTERMOST_IP = "panels/json/mattermost-index-pattern.json"

MATTERMOST_MENU = {
    'name': 'Mattermost',
    'source': MATTERMOST,
    'icon': 'default.png',
    'index-patterns': [MATTERMOST_IP],
    'menu': [
        {'name': 'Overview', 'panel': MATTERMOST_PANEL}
    ]
}


class TaskPanels(Task):
    """
    Upload all the Kibana dashboards/GrimoireLab panels based on
    enabled data sources AND the menu file. Before uploading the panels
    it also sets up common configuration variables for Kibiter
    """

    # Panels which include several data sources
    panels_multi_ds = ["panels/json/overview.json", "panels/json/data_status.json"]
    # Panels to be uploaded always, no matter the data sources configured
    panels_common = panels_multi_ds + ["panels/json/about.json"]

    def __init__(self, conf):
        super().__init__(conf)
        # Read panels and menu description from yaml file
        with open(TaskPanelsMenu.MENU_YAML, 'r') as f:
            try:
                self.panels_menu = yaml.load(f)
            except yaml.YAMLError as ex:
                logger.error(ex)
                raise

        # FIXME exceptions raised here are not handled!!

        # Gets the cross set of enabled data sources and data sources
        # available in the menu file. For the result set gets the file
        # names of dashoards and index pattern to be uploaded
        enabled_ds = conf.get_data_sources()
        self.panels = {}

        for ds in self.panels_menu:
            if ds['source'] not in enabled_ds:
                continue
            for entry in ds['menu']:
                if ds['source'] not in self.panels.keys():
                    self.panels[ds['source']] = []
                self.panels[ds['source']].append(entry['panel'])
            if 'index-patterns' in ds:
                for index_pattern in ds['index-patterns']:
                    self.panels[ds['source']].append(index_pattern)

        if self.conf['panels'][COMMUNITY]:
            self.panels[COMMUNITY] = [ONION_PANEL_OVERALL, ONION_PANEL_PROJECTS,
                                      ONION_PANEL_ORGS, DEMOGRAPHICS,
                                      ONION_PANEL_OVERALL_IP, ONION_PANEL_PROJECTS_IP,
                                      ONION_PANEL_ORGS_IP, DEMOGRAPHICS_IP]

        if self.conf['panels'][KAFKA]:
            self.panels[KAFKA] = [KAFKA_PANEL, KAKFA_IP]

        if self.conf['panels'][GITLAB_ISSUES]:
            self.panels[GITLAB_ISSUES] = [GITLAB_ISSUES_PANEL_BACKLOG, GITLAB_ISSUES_PANEL_OVERALL,
                                          GITLAB_ISSUES_PANEL_TIMING, GITLAB_ISSUES_IP]

        if self.conf['panels'][GITLAB_MERGES]:
            self.panels[GITLAB_MERGES] = [GITLAB_MERGES_PANEL_BACKLOG, GITLAB_MERGES_PANEL_OVERALL,
                                          GITLAB_MERGES_PANEL_TIMING, GITLAB_MERGES_IP]

        if self.conf['panels'][MATTERMOST]:
            self.panels[MATTERMOST] = [MATTERMOST_PANEL, MATTERMOST_IP]

    def is_backend_task(self):
        return False

    def __kibiter_version(self):
        """ Get the kibiter vesion.

        :param major: major Elasticsearch version
        """
        version = None

        es_url = self.conf['es_enrichment']['url']
        config_url = '.kibana/config/_search'
        url = urljoin(es_url + "/", config_url)
        version = None
        try:
            res = self.grimoire_con.get(url)
            res.raise_for_status()
            version = res.json()['hits']['hits'][0]['_id']
            logger.debug("Kibiter version: %s", version)
        except requests.exceptions.HTTPError:
            logger.warning("Can not find Kibiter version")

        return version

    def __configure_kibiter_setting(self, endpoint, data_value=None):
        kibana_headers = copy.deepcopy(ES6_HEADER)
        kibana_headers["kbn-xsrf"] = "true"

        kibana_url = self.conf['panels']['kibiter_url'] + KIBANA_SETTINGS_URL
        endpoint_url = kibana_url + '/' + endpoint

        res = self.grimoire_con.post(endpoint_url, headers=kibana_headers,
                                     data=json.dumps(data_value), verify=False)
        try:
            res.raise_for_status()
        except requests.exceptions.HTTPError:
            logger.error("Impossible to set %s: %s", endpoint, str(res.json()))
            return False

        return True

    def __configure_kibiter_6(self):
        if 'panels' not in self.conf:
            logger.warning("Panels config not availble. Not configuring Kibiter.")
            return False

        # Create .kibana index if not exists
        es_url = self.conf['es_enrichment']['url']
        kibiter_url = self.conf['panels']['kibiter_url']
        check_kibana_index(es_url, kibiter_url)

        # set default index pattern
        kibiter_default_index = self.conf['panels']['kibiter_default_index']
        data_value = {"value": kibiter_default_index}
        defaultIndexFlag = self.__configure_kibiter_setting('defaultIndex',
                                                            data_value=data_value)

        # set default time picker
        kibiter_time_from = self.conf['panels']['kibiter_time_from']
        time_picker = {"from": kibiter_time_from, "to": "now", "mode": "quick"}
        data_value = {"value": json.dumps(time_picker)}
        timePickerFlag = self.__configure_kibiter_setting('timepicker:timeDefaults',
                                                          data_value=data_value)

        if defaultIndexFlag and timePickerFlag:
            logger.info("Kibiter settings configured!")
            return True

        logger.error("Kibiter settings not configured!")
        return False

    def __configure_kibiter_old(self, kibiter_major):

        if 'panels' not in self.conf:
            logger.warning("Panels config not availble. Not configuring Kibiter.")
            return False

        kibiter_time_from = self.conf['panels']['kibiter_time_from']
        kibiter_default_index = self.conf['panels']['kibiter_default_index']

        logger.info("Configuring Kibiter %s for default index %s and time frame %s",
                    kibiter_major, kibiter_default_index, kibiter_time_from)

        kibiter_version = self.__kibiter_version()
        if not kibiter_version:
            return False
        logger.info("Kibiter/Kibana: version found is %s" % kibiter_version)
        time_picker = "{\n  \"from\": \"" + kibiter_time_from \
            + "\",\n  \"to\": \"now\",\n  \"mode\": \"quick\"\n}"

        config_resource = '.kibana/config/' + kibiter_version
        kibiter_config = {
            "defaultIndex": kibiter_default_index,
            "timepicker:timeDefaults": time_picker
        }

        es_url = self.conf['es_enrichment']['url']
        url = urljoin(es_url + "/", config_resource)
        res = self.grimoire_con.post(url, data=json.dumps(kibiter_config),
                                     headers=ES6_HEADER)
        res.raise_for_status()

        logger.info("Kibiter settings configured!")
        return True

    def create_dashboard(self, panel_file, data_sources=None, strict=True):
        """Upload a panel to Elasticsearch if it does not exist yet.

        If a list of data sources is specified, upload only those
        elements (visualizations, searches) that match that data source.

        :param panel_file: file name of panel (dashobard) to upload
        :param data_sources: list of data sources
        :param strict: only upload a dashboard if it is newer than the one already existing
        """
        es_enrich = self.conf['es_enrichment']['url']
        kibana_url = self.conf['panels']['kibiter_url']

        mboxes_sources = set(['pipermail', 'hyperkitty', 'groupsio', 'nntp'])
        if data_sources and any(x in data_sources for x in mboxes_sources):
            data_sources = list(data_sources)
            data_sources.append('mbox')
        if data_sources and ('supybot' in data_sources):
            data_sources = list(data_sources)
            data_sources.append('irc')
        if data_sources and 'google_hits' in data_sources:
            data_sources = list(data_sources)
            data_sources.append('googlehits')
        if data_sources and 'stackexchange' in data_sources:
            # stackexchange is called stackoverflow in panels
            data_sources = list(data_sources)
            data_sources.append('stackoverflow')
        if data_sources and 'phabricator' in data_sources:
            data_sources = list(data_sources)
            data_sources.append('maniphest')

        try:
            import_dashboard(es_enrich, kibana_url, panel_file, data_sources=data_sources, strict=strict)
        except ValueError:
            logger.error("%s does not include release field. Not loading the panel.", panel_file)
        except RuntimeError:
            logger.error("Can not load the panel %s", panel_file)

    def execute(self):
        # Configure kibiter
        kibiter_major = self.es_version(self.conf['es_enrichment']['url'])
        strict_loading = self.conf['panels'][STRICT_LOADING]

        if kibiter_major < "6":
            self.__configure_kibiter_old(kibiter_major)
        else:
            self.__configure_kibiter_6()

        logger.info("Dashboard panels, visualizations: uploading...")
        # Create the commons panels
        for panel_file in self.panels_common:
            data_sources = None  # for some panels, only the active data sources must be included
            if panel_file in TaskPanels.panels_multi_ds:
                data_sources = self.panels.keys()
            self.create_dashboard(panel_file, data_sources=data_sources, strict=strict_loading)

        # Upload all the Kibana dashboards/GrimoireLab panels based on
        # enabled data sources AND the menu file
        for ds in self.panels:
            for panel_file in self.panels[ds]:
                try:
                    self.create_dashboard(panel_file, strict=strict_loading)
                except Exception as ex:
                    logger.error("%s not correctly uploaded (%s)", panel_file, ex)
        logger.info("Dashboard panels, visualizations: uploaded!")


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
            "raw": ["google-hits-raw"],
            "enrich": ["google-hits", "google-hits_enrich"]
        },
        "jenkins": {
            "raw": ["jenkins-raw"],
            "enrich": ["jenkins", "jenkins_enrich"]
        },
        "mbox": {
            "raw": ["mbox-raw"],
            "enrich": ["mbox", "mbox_enrich", "kafka"]
        },
        "pipermail": {
            "raw": ["pipermail-raw"],
            "enrich": ["mbox", "mbox_enrich", "kafka"]
        },
        "hyperkitty": {
            "raw": ["hyperkitty-raw"],
            "enrich": ["mbox", "mbox_enrich", "kafka"]
        },
        "nntp": {
            "raw": ["nntp-raw"],
            "enrich": ["mbox", "mbox_enrich", "kafka"]
        },
        "groupsio": {
            "raw": ["groupsio-raw"],
            "enrich": ["mbox", "mbox_enrich", "kafka"]
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
        "gitlab:issue": {
            "raw": ["gitlab_issue-raw"],
            "enrich": ["gitlab", "gitlab_issue"]
        },
        "gitlab:merge": {
            "raw": ["gitlab_merge-raw"],
            "enrich": ["gitlab_merge"]
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
        """Create aliases in ElasticSearch used by the panels"""

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
        """Create the aliases"""

        logger.info("Elasticsearch aliases for {}: creating...".format(self.backend_section))
        self.__create_aliases()
        logger.info("Elasticsearch aliases for {}: created!".format(self.backend_section))


class TaskPanelsMenu(Task):
    """Create the menu to access the panels"""

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

        if self.conf['panels'][COMMUNITY]:
            self.panels_menu.append(COMMUNITY_MENU)

        if self.conf['panels'][KAFKA]:
            self.panels_menu.append(KAFKA_MENU)

        if self.conf['panels'][GITLAB_ISSUES]:
            self.panels_menu.append(GITLAB_ISSUES_MENU)

        if self.conf['panels'][GITLAB_MERGES]:
            self.panels_menu.append(GITLAB_MERGES_MENU)

        if self.conf['panels'][MATTERMOST]:
            self.panels_menu.append(MATTERMOST_MENU)

        # Get the active data sources
        self.data_sources = self.__get_active_data_sources()
        if 'short_name' in self.conf['general']:
            self.project_name = self.conf['general']['short_name']
        else:
            self.project_name = 'GrimoireLab'

    def is_backend_task(self):
        return False

    def __get_active_data_sources(self):
        active_ds = []
        for entry in self.panels_menu:
            ds = entry['source']
            if ds in self.conf.keys() or ds in [COMMUNITY, KAFKA, GITLAB_ISSUES, GITLAB_MERGES, MATTERMOST]:
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
        """Create the menu definition to access the panels in a dashboard.

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

        mapping_url = urljoin(self.conf['es_enrichment']['url'] + "/",
                              mapping_resource)
        logger.debug("Adding mapping for metadashboard")
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
        """Remove existing menu for dashboard, if any.

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

    def __get_menu_entries(self, kibiter_major):
        """ Get the menu entries from the panel definition """
        menu_entries = OrderedDict()
        for entry in self.panels_menu:
            if entry['source'] not in self.data_sources:
                continue
            menu_entries[entry['name']] = OrderedDict()
            for subentry in entry['menu']:
                try:
                    dash_name = get_dashboard_name(subentry['panel'])
                except FileNotFoundError:
                    logging.error("Can't open dashboard file %s", subentry['panel'])
                    continue
                # The name for the entry is in self.panels_menu
                menu_entries[entry['name']][subentry['name']] = dash_name

        return menu_entries

    def __get_dash_menu(self, kibiter_major):
        """Order the dashboard menu"""

        omenu = OrderedDict()
        # Start with Overview
        omenu["Overview"] = self.menu_panels_common['Overview']

        # Now the data _getsources
        ds_menu = self.__get_menu_entries(kibiter_major)
        omenu.update(ds_menu)

        # At the end Data Status, About
        omenu["Data Status"] = self.menu_panels_common['Data Status']
        omenu["About"] = self.menu_panels_common['About']

        logger.debug("Menu for panels: %s", json.dumps(ds_menu, indent=4))
        return omenu

    def execute(self):
        kibiter_major = self.es_version(self.conf['es_enrichment']['url'])

        logger.info("Dashboard menu: uploading for %s ..." % kibiter_major)
        # Create the panels menu
        menu = self.__get_dash_menu(kibiter_major)
        # Remove the current menu and create the new one
        self.__upload_title(kibiter_major)
        self.__remove_dashboard_menu(kibiter_major)
        self.__create_dashboard_menu(menu, kibiter_major)
        logger.info("Dashboard menu: uploaded!")
