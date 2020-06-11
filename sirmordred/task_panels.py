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
from grimoirelab_toolkit.uris import urijoin

from kidash.kidash import import_dashboard, get_dashboard_name, check_kibana_index
from sirmordred.task import Task

logger = logging.getLogger(__name__)

# Header mandatory in ElasticSearch 6
ES6_HEADER = {"Content-Type": "application/json"}
KIBANA_SETTINGS_URL = '/api/kibana/settings'

STRICT_LOADING = "strict"

KAFKA_NAME = 'KIP'
KAFKA_SOURCE = "kafka"
KAFKA_PANEL = "panels/json/kip.json"
KAKFA_IP = "panels/json/kafka-index-pattern.json"

KAFKA_MENU = {
    'name': KAFKA_NAME,
    'source': KAFKA_SOURCE,
    'icon': 'default.png',
    'index-patterns': [KAKFA_IP],
    'menu': [
        {'name': 'Overview', 'panel': KAFKA_PANEL}
    ]
}

COMMUNITY_NAME = 'Community'
COMMUNITY_SOURCE = 'community'
ONION_PANEL_OVERALL = 'panels/json/onion_overall.json'
ONION_PANEL_PROJECTS = 'panels/json/onion_projects.json'
ONION_PANEL_ORGS = 'panels/json/onion_organizations.json'
DEMOGRAPHICS = 'panels/json/demographics.json'
AFFILIATIONS = 'panels/json/affiliations.json'
CONTRIBUTIONS_GROWTH = 'panels/json/contributors_growth.json'
ENGAGEMENT_BY_CONTRIBUTIONS = 'panels/json/engagement_by_contributions.json'
ORGANIZATIONAL_DIVERSITY = 'panels/json/organizational_diversity.json'
ORGANIZATIONAL_DIVERSITY_BY_DOMAINS = 'panels/json/organizational_diversity_by_domains.json'

ONION_PANEL_OVERALL_IP = 'panels/json/all_onion-index-pattern.json'
ONION_PANEL_PROJECTS_IP = 'panels/json/all_onion-index-pattern.json'
ONION_PANEL_ORGS_IP = 'panels/json/all_onion-index-pattern.json'
DEMOGRAPHICS_IP = 'panels/json/demographics-index-pattern.json'
AFFILIATIONS_IP = 'panels/json/affiliations-index-pattern.json'
ALL_ENRICHED_IP = 'panels/json/all_enriched-index-pattern.json'
ALL_ENRICHED_TICKETS_IP = 'panels/json/all_enriched_tickets-index-pattern.json'

COMMUNITY_MENU = {
    'name': COMMUNITY_NAME,
    'source': COMMUNITY_SOURCE,
    'icon': 'default.png',
    'index-patterns': [
        ONION_PANEL_OVERALL_IP,
        ONION_PANEL_PROJECTS_IP,
        ONION_PANEL_ORGS_IP,
        DEMOGRAPHICS_IP,
        AFFILIATIONS_IP,
        ALL_ENRICHED_IP,
        ALL_ENRICHED_TICKETS_IP
    ],
    'menu': [
        {'name': 'Overall', 'panel': ONION_PANEL_OVERALL},
        {'name': 'Projects', 'panel': ONION_PANEL_PROJECTS},
        {'name': 'Organizations', 'panel': ONION_PANEL_ORGS},
        {'name': 'Demographics', 'panel': DEMOGRAPHICS},
        {'name': 'Affiliations', 'panel': AFFILIATIONS},
        {'name': 'Contributors Growth', 'panel': CONTRIBUTIONS_GROWTH},
        {'name': 'Organizational Diversity', 'panel': ORGANIZATIONAL_DIVERSITY},
        {'name': 'Organizational Diversity by Domains', 'panel': ORGANIZATIONAL_DIVERSITY_BY_DOMAINS},
        {'name': 'Engagement', 'panel': ENGAGEMENT_BY_CONTRIBUTIONS}
    ]
}

GITHUB_COMMENTS = "github-comments"
GITHUB_ISSUE_COMMENTS_PANEL = "panels/json/github2_issues_comments_and_collaboration.json"
GITHUB_ISSUE_COMMENTS_IP = "panels/json/github2_issues-index-pattern.json"
GITHUB_PULL_COMMENTS_PANEL = "panels/json/github2_pull_requests_comments_and_collaboration.json"
GITHUB_PULL_COMMENTS_IP = "panels/json/github2_pull_requests-index-pattern.json"

GITHUB_COMMENTS_MENU = {
    'name': 'GitHub Comments',
    'source': GITHUB_COMMENTS,
    'icon': 'default.png',
    'index-patterns': [GITHUB_ISSUE_COMMENTS_IP, GITHUB_PULL_COMMENTS_IP],
    'menu': [
        {'name': 'Issues', 'panel': GITHUB_ISSUE_COMMENTS_PANEL},
        {'name': 'Pull requests', 'panel': GITHUB_PULL_COMMENTS_PANEL}
    ]
}

GITHUB_EVENTS = "github-events"
GITHUB_CLOSED_EVENTS_PANEL = "panels/json/github_events_closed.json"
GITHUB_LABEL_EVENTS_PANEL = "panels/json/github_events_labels.json"
GITHUB_EVENTS_IP = "panels/json/github_events-index-pattern.json"

GITHUB_EVENTS_MENU = {
    'name': 'GitHub Events',
    'source': GITHUB_EVENTS,
    'icon': 'default.png',
    'index-patterns': [GITHUB_EVENTS_IP],
    'menu': [
        {'name': 'Closed events', 'panel': GITHUB_CLOSED_EVENTS_PANEL},
        {'name': 'Label events', 'panel': GITHUB_LABEL_EVENTS_PANEL}
    ]
}

GITHUB_REPOS = "github-repos"
GITHUB_REPOS_PANEL_OVERALL = "panels/json/github_repositories.json"
GITHUB_REPOS_IP = "panels/json/github_repositories-index-pattern.json"

GITHUB_REPOS_MENU = {
    'name': 'GitHub Repositories',
    'source': GITHUB_REPOS,
    'icon': 'default.png',
    'index-patterns': [GITHUB_REPOS_IP],
    'menu': [
        {'name': 'Overview', 'panel': GITHUB_REPOS_PANEL_OVERALL}
    ]
}

GITLAB_ISSUES = "gitlab-issues"
GITLAB_ISSUES_PANEL_OVERALL = "panels/json/gitlab_issues.json"
GITLAB_ISSUES_PANEL_BACKLOG = "panels/json/gitlab_issues_backlog.json"
GITLAB_ISSUES_PANEL_TIMING = "panels/json/gitlab_issues_timing.json"
GITLAB_ISSUES_PANEL_EFFICIENCY = "panels/json/gitlab_issues_efficiency.json"
GITLAB_ISSUES_IP = "panels/json/gitlab_issues-index-pattern.json"

GITLAB_ISSUES_MENU = {
    'name': 'GitLab Issues',
    'source': GITLAB_ISSUES,
    'icon': 'default.png',
    'index-patterns': [GITLAB_ISSUES_IP],
    'menu': [
        {'name': 'Overview', 'panel': GITLAB_ISSUES_PANEL_OVERALL},
        {'name': 'Backlog', 'panel': GITLAB_ISSUES_PANEL_BACKLOG},
        {'name': 'Timing', 'panel': GITLAB_ISSUES_PANEL_TIMING},
        {'name': 'Efficiency', 'panel': GITLAB_ISSUES_PANEL_EFFICIENCY}
    ]
}

GITLAB_MERGES = "gitlab-merges"
GITLAB_MERGES_PANEL_OVERALL = "panels/json/gitlab_merge_requests.json"
GITLAB_MERGES_PANEL_BACKLOG = "panels/json/gitlab_merge_requests_backlog.json"
GITLAB_MERGES_PANEL_TIMING = "panels/json/gitlab_merge_requests_timing.json"
GITLAB_MERGES_PANEL_EFFICIENCY = "panels/json/gitlab_merge_requests_efficiency.json"
GITLAB_MERGES_IP = "panels/json/gitlab_merge_requests-index-pattern.json"

GITLAB_MERGES_MENU = {
    'name': 'GitLab Merges',
    'source': GITLAB_MERGES,
    'icon': 'default.png',
    'index-patterns': [GITLAB_MERGES_IP],
    'menu': [
        {'name': 'Overview', 'panel': GITLAB_MERGES_PANEL_OVERALL},
        {'name': 'Backlog', 'panel': GITLAB_MERGES_PANEL_BACKLOG},
        {'name': 'Timing', 'panel': GITLAB_MERGES_PANEL_TIMING},
        {'name': 'Efficiency', 'panel': GITLAB_MERGES_PANEL_EFFICIENCY}
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

MATTERMOST = "mattermost"
MATTERMOST_PANEL = "panels/json/mattermost.json"
MATTERMOST_IP = "panels/json/mattermost-index-pattern.json"

COCOM_NAME = 'Code Complexity'
COCOM_SOURCE = 'code-complexity'
COCOM_PANEL = "panels/json/cocom.json"
COCOM_IP = "panels/json/cocom-index-pattern.json"
COCOM_STUDY_IP = "panels/json/cocom_study-index-pattern.json"

COCOM_MENU = {
    'name': COCOM_NAME,
    'source': COCOM_SOURCE,
    'icon': 'default.png',
    'index-patterns': [
        COCOM_IP,
        COCOM_STUDY_IP
    ],
    'menu': [
        {'name': 'Overview', 'panel': COCOM_PANEL}
    ]
}

COLIC_NAME = 'Code License'
COLIC_SOURCE = 'code-license'
COLIC_PANEL = "panels/json/colic.json"
COLIC_IP = "panels/json/colic-index-pattern.json"
COLIC_STUDY_IP = "panels/json/colic_study-index-pattern.json"

COLIC_MENU = {
    'name': COLIC_NAME,
    'source': COLIC_SOURCE,
    'icon': 'default.png',
    'index-patterns': [
        COLIC_IP,
        COLIC_STUDY_IP
    ],
    'menu': [
        {'name': 'Overview', 'panel': COLIC_PANEL}
    ]
}


def get_sigils_path():
    sigils_path = panels.__file__.replace('panels/__init__.py', '')
    return sigils_path


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
        with open(self.conf['general']['menu_file'], 'r') as f:
            try:
                self.panels_menu = yaml.load(f, Loader=yaml.SafeLoader)
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

        if self.conf['panels'][COMMUNITY_SOURCE]:
            self.panels[COMMUNITY_SOURCE] = [ONION_PANEL_OVERALL, ONION_PANEL_PROJECTS,
                                             ONION_PANEL_ORGS, DEMOGRAPHICS, AFFILIATIONS,
                                             ONION_PANEL_OVERALL_IP, ONION_PANEL_PROJECTS_IP,
                                             ONION_PANEL_ORGS_IP, DEMOGRAPHICS_IP, AFFILIATIONS_IP,
                                             ENGAGEMENT_BY_CONTRIBUTIONS, CONTRIBUTIONS_GROWTH,
                                             ORGANIZATIONAL_DIVERSITY, ORGANIZATIONAL_DIVERSITY_BY_DOMAINS,
                                             ALL_ENRICHED_IP, ALL_ENRICHED_TICKETS_IP]

        if self.conf['panels'][KAFKA_SOURCE]:
            self.panels[KAFKA_SOURCE] = [KAFKA_PANEL, KAKFA_IP]

        if self.conf['panels'][GITHUB_COMMENTS]:
            self.panels[GITHUB_COMMENTS] = [GITHUB_ISSUE_COMMENTS_PANEL, GITHUB_PULL_COMMENTS_PANEL,
                                            GITHUB_ISSUE_COMMENTS_IP, GITHUB_PULL_COMMENTS_IP]

        if self.conf['panels'][GITHUB_EVENTS]:
            self.panels[GITHUB_EVENTS] = [GITHUB_CLOSED_EVENTS_PANEL, GITHUB_LABEL_EVENTS_PANEL, GITHUB_EVENTS_IP]

        if self.conf['panels'][GITHUB_REPOS]:
            self.panels[GITHUB_REPOS] = [GITHUB_REPOS_PANEL_OVERALL, GITHUB_REPOS_IP]

        if self.conf['panels'][GITLAB_ISSUES]:
            self.panels[GITLAB_ISSUES] = [GITLAB_ISSUES_PANEL_BACKLOG, GITLAB_ISSUES_PANEL_OVERALL,
                                          GITLAB_ISSUES_PANEL_TIMING, GITLAB_ISSUES_PANEL_EFFICIENCY,
                                          GITLAB_ISSUES_IP]

        if self.conf['panels'][GITLAB_MERGES]:
            self.panels[GITLAB_MERGES] = [GITLAB_MERGES_PANEL_BACKLOG, GITLAB_MERGES_PANEL_OVERALL,
                                          GITLAB_MERGES_PANEL_TIMING, GITLAB_MERGES_PANEL_EFFICIENCY,
                                          GITLAB_MERGES_IP]

        if self.conf['panels'][MATTERMOST]:
            self.panels[MATTERMOST] = [MATTERMOST_PANEL, MATTERMOST_IP]

        if self.conf['panels'][COCOM_SOURCE]:
            self.panels[COCOM_SOURCE] = [COCOM_PANEL, COCOM_IP, COCOM_STUDY_IP]

        if self.conf['panels'][COLIC_SOURCE]:
            self.panels[COLIC_SOURCE] = [COLIC_PANEL, COLIC_IP, COLIC_STUDY_IP]

    def is_backend_task(self):
        return False

    def __configure_kibiter_setting(self, endpoint, data_value=None):
        kibana_headers = copy.deepcopy(ES6_HEADER)
        kibana_headers["kbn-xsrf"] = "true"

        kibana_url = self.conf['panels']['kibiter_url'] + KIBANA_SETTINGS_URL
        endpoint_url = kibana_url + '/' + endpoint

        try:
            res = self.grimoire_con.post(endpoint_url, headers=kibana_headers,
                                         data=json.dumps(data_value), verify=False)
            res.raise_for_status()
        except requests.exceptions.HTTPError:
            logger.error("Impossible to set %s: %s", endpoint, str(res.json()))
            return False
        except requests.exceptions.ConnectionError as ex:
            logger.error("Impossible to connect to kibiter %s: %s",
                         self.anonymize_url(self.conf['panels']['kibiter_url']), ex)
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

        panels_path = get_sigils_path() + panel_file
        try:
            import_dashboard(es_enrich, kibana_url, panels_path, data_sources=data_sources, strict=strict)
        except ValueError:
            logger.error("%s does not include release field. Not loading the panel.", panels_path)
        except RuntimeError:
            logger.error("Can not load the panel %s", panels_path)

    def execute(self):
        # Configure kibiter
        kibiter_major = self.es_version(self.conf['es_enrichment']['url'])
        strict_loading = self.conf['panels'][STRICT_LOADING]

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


class TaskPanelsMenu(Task):
    """Create the menu to access the panels"""

    menu_panels_common = {
        "Overview": {
            "title": "Overview",
            "name": "Overview",
            "description": "Overview panel",
            "type": "entry",
            "panel_id": "Overview"
        },
        "Data Status": {
            "title": "Data Status",
            "name": "Data Status",
            "description": "Data Status panel",
            "type": "entry",
            "panel_id": "Data-Status"
        }
    }

    def __init__(self, conf):
        super().__init__(conf)
        # Read panels and menu description from yaml file """
        with open(self.conf['general']['menu_file'], 'r') as f:
            try:
                self.panels_menu = yaml.load(f, Loader=yaml.SafeLoader)
            except yaml.YAMLError as ex:
                logger.error(ex)
                raise

        if self.conf['panels'][GITHUB_COMMENTS]:
            self.panels_menu.append(GITHUB_COMMENTS_MENU)

        if self.conf['panels'][GITHUB_EVENTS]:
            self.panels_menu.append(GITHUB_EVENTS_MENU)

        if self.conf['panels'][GITHUB_REPOS]:
            self.panels_menu.append(GITHUB_REPOS_MENU)

        if self.conf['panels'][GITLAB_ISSUES]:
            self.panels_menu.append(GITLAB_ISSUES_MENU)

        if self.conf['panels'][GITLAB_MERGES]:
            self.panels_menu.append(GITLAB_MERGES_MENU)

        if self.conf['panels'][MATTERMOST]:
            self.panels_menu.append(MATTERMOST_MENU)

        if self.conf['panels'][COMMUNITY_SOURCE]:
            self.panels_menu.append(COMMUNITY_MENU)

        if self.conf['panels'][KAFKA_SOURCE]:
            self.panels_menu.append(KAFKA_MENU)

        if self.conf['panels'][COCOM_SOURCE]:
            self.panels_menu.append(COCOM_MENU)

        if self.conf['panels'][COLIC_SOURCE]:
            self.panels_menu.append(COLIC_MENU)

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
            if ds in self.conf.keys() or ds in [COMMUNITY_SOURCE, KAFKA_SOURCE, GITLAB_ISSUES, GITLAB_MERGES,
                                                MATTERMOST, GITHUB_COMMENTS, GITHUB_REPOS, GITHUB_EVENTS,
                                                COCOM_SOURCE, COLIC_SOURCE]:
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
        resource = ".kibana/doc/projectname"
        data = {"projectname": {"name": self.project_name}}
        mapping_resource = ".kibana/_mapping/doc"
        mapping = {"dynamic": "true"}

        url = urijoin(self.conf['es_enrichment']['url'], resource)
        mapping_url = urijoin(self.conf['es_enrichment']['url'],
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
        menu_resource = ".kibana/doc/metadashboard"
        mapping_resource = ".kibana/_mapping/doc"
        mapping = {"dynamic": "true"}
        menu = {'metadashboard': dash_menu}
        menu_url = urijoin(self.conf['es_enrichment']['url'],
                           menu_resource)

        mapping_url = urijoin(self.conf['es_enrichment']['url'],
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
        metadashboard = ".kibana/doc/metadashboard"
        menu_url = urijoin(self.conf['es_enrichment']['url'], metadashboard)
        self.grimoire_con.delete(menu_url)

    def __get_menu_entries(self, kibiter_major):
        """ Get the menu entries from the panel definition """
        menu_entries = []
        for entry in self.panels_menu:
            if entry['source'] not in self.data_sources:
                continue
            parent_menu_item = {
                'name': entry['name'],
                'title': entry['name'],
                'description': "",
                'type': "menu",
                'dashboards': []
            }
            for subentry in entry['menu']:
                try:
                    panel_path = get_sigils_path() + subentry['panel']
                    dash_name = get_dashboard_name(panel_path)
                except FileNotFoundError:
                    logging.error("Can't open dashboard file %s", subentry['panel'])
                    continue
                # The name for the entry is in self.panels_menu
                child_item = {
                    "name": subentry['name'],
                    "title": subentry['name'],
                    "description": "",
                    "type": "entry",
                    "panel_id": dash_name
                }
                parent_menu_item['dashboards'].append(child_item)
            menu_entries.append(parent_menu_item)

        return menu_entries

    def __get_about_menu(self, contact_link):
        """ Fill About entry with the panel and the contact link """
        about_menu_item = {
            'name': 'About',
            'title': 'About',
            'description': "About menu",
            'type': "menu",
            'dashboards': [
                {
                    "title": "About the dashboard",
                    "name": "About the dashboard",
                    "description": "Panel with information about the usage of the interface, an information about the \
                                    panel itself and acknowledgments",
                    "type": "entry",
                    "panel_id": "About"
                }
            ]
        }

        if contact_link:
            contact_entry = {
                "title": "Contact",
                "name": "Contact",
                "description": "Direct link to the support repository",
                "type": "entry",
                "panel_id": contact_link
            }
            about_menu_item['dashboards'].append(contact_entry)

        return about_menu_item

    def __get_dash_menu(self, kibiter_major, contact_link):
        """Order the dashboard menu"""

        # omenu = OrderedDict()
        omenu = []
        # Start with Overview
        omenu.append(self.menu_panels_common['Overview'])

        # Now the data _getsources
        ds_menu = self.__get_menu_entries(kibiter_major)

        # Remove the kafka and community menus, they will be included at the end
        kafka_menu = None
        community_menu = None
        cocom_menu = None
        colic_menu = None

        found_cocom = [pos for pos, menu in enumerate(ds_menu) if menu['name'] == COCOM_NAME]
        if found_cocom:
            cocom_menu = ds_menu.pop(found_cocom[0])

        found_colic = [pos for pos, menu in enumerate(ds_menu) if menu['name'] == COLIC_NAME]
        if found_colic:
            colic_menu = ds_menu.pop(found_colic[0])

        found_kafka = [pos for pos, menu in enumerate(ds_menu) if menu['name'] == KAFKA_NAME]
        if found_kafka:
            kafka_menu = ds_menu.pop(found_kafka[0])

        found_community = [pos for pos, menu in enumerate(ds_menu) if menu['name'] == COMMUNITY_NAME]
        if found_community:
            community_menu = ds_menu.pop(found_community[0])

        ds_menu.sort(key=operator.itemgetter('name'))
        omenu += ds_menu

        # If kafka and community are present add them before the Data Status and About
        if kafka_menu:
            omenu.append(kafka_menu)

        if cocom_menu:
            omenu.append(cocom_menu)

        if colic_menu:
            omenu.append(colic_menu)

        if community_menu:
            omenu.append(community_menu)

        # At the end Data Status
        omenu.append(self.menu_panels_common['Data Status'])

        # And About
        omenu.append(self.__get_about_menu(contact_link))

        logger.debug("Menu for panels: %s", json.dumps(ds_menu, indent=4))
        return omenu

    def execute(self):
        kibiter_major = self.es_version(self.conf['es_enrichment']['url'])

        logger.info("Dashboard menu: uploading for %s ..." % kibiter_major)
        # Create the panels menu
        menu = self.__get_dash_menu(kibiter_major, self.conf['panels']['contact'])
        # Remove the current menu and create the new one
        self.__upload_title(kibiter_major)
        self.__remove_dashboard_menu(kibiter_major)
        self.__create_dashboard_menu(menu, kibiter_major)
        logger.info("Dashboard menu: uploaded!")
