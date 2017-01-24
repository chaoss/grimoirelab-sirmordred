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

import configparser
import logging
import time
import threading
import json
import sys
import requests

import yaml

from collections import OrderedDict
from datetime import datetime, timedelta

from urllib.parse import urljoin

from grimoire_elk.arthur import (feed_backend, enrich_backend, get_ocean_backend,
                                 load_identities, do_studies,
                                 refresh_projects, refresh_identities)
from grimoire_elk.panels import import_dashboard, get_dashboard_name
from grimoire_elk.utils import get_connectors, get_connector_from_name, get_elastic

from sortinghat import api
from sortinghat.cmd.affiliate import Affiliate
from sortinghat.cmd.autoprofile import AutoProfile
from sortinghat.cmd.init import Init
from sortinghat.cmd.load import Load
from sortinghat.cmd.unify import Unify
from sortinghat.command import CMD_SUCCESS
from sortinghat.db.database import Database
from sortinghat.db.model import Profile



SLEEPFOR_ERROR = """Error: You may be Arthur, King of the Britons. But you still """ + \
"""need the 'sleep_for' variable in sortinghat section\n - Mordred said."""
ES_ERROR = "Before starting to seek the Holy Grail, make sure your ElasticSearch " + \
"at '%(uri)s' is available!!\n - Mordred said."

logger = logging.getLogger(__name__)

class Task():
    """ Basic class shared by all tasks """

    ES_INDEX_FIELDS = ['enriched_index', 'raw_index', 'es_collection_url']

    def __init__(self, conf):
        self.conf = conf
        self.db_sh = self.conf['sh_database']
        self.db_user = self.conf['sh_user']
        self.db_password = self.conf['sh_password']
        self.db_host = self.conf['sh_host']

    def compose_p2o_params(self, backend_name, repo):
        # get p2o params included in the projects list
        params = {}

        connector = get_connector_from_name(self.backend_name)
        ocean = connector[1]

        # First add the params from the URL, which is backend specific
        params = ocean.get_p2o_params_from_url(repo)

        return params


    def compose_perceval_params(self, backend_name, repo):
        # Params that are lists separated by white space
        list_params_spaces = ['blacklist-jobs']

        connector = get_connector_from_name(self.backend_name)
        ocean = connector[1]

        # First add the params from the URL, which is backend specific
        params = ocean.get_perceval_params_from_url(repo)

        # Now add the backend params included in the config file
        for p in self.conf[backend_name]:
            if p in self.ES_INDEX_FIELDS:
                # These params are not for the perceval backend
                continue
            params.append("--"+p)
            if self.conf[backend_name][p]:
                if type(self.conf[backend_name][p]) != bool:
                    if p in list_params_spaces:
                        # '--blacklist-jobs', 'a', 'b', 'c'
                        # 'a', 'b', 'c' must be added as items in the list
                        list_params = self.conf[backend_name][p].split()
                        params += list_params
                    else:
                        params.append(self.conf[backend_name][p])
        return params

    def _get_collection_url(self):
        es_col_url = self.conf['es_collection']
        if 'es_collection_url' in self.conf[self.backend_name]:
            es_col_url = self.conf[self.backend_name]['es_collection_url']
        return es_col_url

    def get_enrich_backend(self):
        db_projects_map = None
        json_projects_map = None
        clean = False
        connector = get_connector_from_name(self.backend_name)

        enrich_backend = connector[2](self.db_sh, db_projects_map, json_projects_map,
                                      self.db_user, self.db_password, self.db_host)
        elastic_enrich = get_elastic(self.conf['es_enrichment'],
                                     self.conf[self.backend_name]['enriched_index'],
                                     clean, enrich_backend)
        enrich_backend.set_elastic(elastic_enrich)

        if 'github' in self.conf.keys() and \
            'backend_token' in self.conf['github'].keys() and \
            self.backend_name == "git":

            gh_token = self.conf['github']['backend_token']
            enrich_backend.set_github_token(gh_token)

        return enrich_backend

    def _get_ocean_backend(self, enrich_backend):
        backend_cmd = None

        no_incremental = False
        clean = False

        ocean_backend = get_ocean_backend(backend_cmd, enrich_backend, no_incremental)
        elastic_ocean = get_elastic(self._get_collection_url(),
                                    self.conf[self.backend_name]['raw_index'],
                                    clean, ocean_backend)
        ocean_backend.set_elastic(elastic_ocean)

        return ocean_backend

    def set_repos(self, repos):
        self.repos = repos

    def set_backend_name(self, backend_name):
        self.backend_name = backend_name

    def is_backend_task(self):
        """
        Returns True if the Task is executed per backend.
        i.e. SortingHat unify is not executed per backend.
        """
        return True

    def run(self):
        """ Execute the Task """
        logger.debug("A bored task. It does nothing!")


class TaskIdentitiesCollection(Task):
    """ Class aimed to get identites from raw data """

    def __init__(self, conf, load_ids=True):
        super().__init__(conf)

        #self.load_orgs = self.conf['sh_load_orgs']  # Load orgs from file
        self.load_ids = load_ids  # Load identities from raw index
        #self.unify = unify  # Unify identities
        #self.autoprofile = autoprofile  # Execute autoprofile
        #self.affiliate = affiliate # Affiliate identities
        self.sh_kwargs={'user': self.db_user, 'password': self.db_password,
                        'database': self.db_sh, 'host': self.db_host,
                        'port': None}

    def run(self):

        #FIXME this should be called just once
        # code = 0 when command success
        code = Init(**self.sh_kwargs).run(self.db_sh)

        if not self.backend_name:
            logger.error ("Backend not configured in TaskIdentitiesCollection.")
            return

        if self.load_ids:
            logger.info("[%s] Gathering identities from raw data" % self.backend_name)
            enrich_backend = self.get_enrich_backend()
            ocean_backend = self._get_ocean_backend(enrich_backend)
            load_identities(ocean_backend, enrich_backend)
            #FIXME get the number of ids gathered


class TaskIdentitiesInit(Task):
    """ Basic class shared by all Sorting Hat tasks """

    def __init__(self, conf):
        super().__init__(conf)

        self.load_orgs = self.conf['sh_load_orgs']  # Load orgs from file
        self.sh_kwargs={'user': self.db_user, 'password': self.db_password,
                        'database': self.db_sh, 'host': self.db_host,
                        'port': None}

    def is_backend_task(self):
        return False

    def run(self):

        # code = 0 when command success
        code = Init(**self.sh_kwargs).run(self.db_sh)

        if self.load_orgs:
            logger.info("[sortinghat] Loading orgs from file %s", self.conf['sh_orgs_file'])
            code = Load(**self.sh_kwargs).run("--orgs", self.conf['sh_orgs_file'])
            if code != CMD_SUCCESS:
                logger.error("[sortinghat] Error loading %s", self.conf['sh_orgs_file'])
            #FIXME get the number of loaded orgs

        if 'sh_ids_file' in self.conf.keys():
            filenames = self.conf['sh_ids_file'].split(',')
            for f in filenames:
                logger.info("[sortinghat] Loading identities from file %s", f)
                f = f.replace(' ','')
                code = Load(**self.sh_kwargs).run("--identities", f )
                if code != CMD_SUCCESS:
                    logger.error("[sortinghat] Error loading %s", f)


class TaskIdentitiesMerge(Task):
    """ Basic class shared by all Sorting Hat tasks """

    def __init__(self, conf, load_orgs=True, load_ids=True, unify=True,
                 autoprofile=True, affiliate=True, bots=True):
        super().__init__(conf)

        self.load_ids = load_ids  # Load identities from raw index
        self.unify = unify  # Unify identities
        self.autoprofile = autoprofile  # Execute autoprofile
        self.affiliate = affiliate # Affiliate identities
        self.bots = bots # Mark bots in SH
        self.sh_kwargs={'user': self.db_user, 'password': self.db_password,
                        'database': self.db_sh, 'host': self.db_host,
                        'port': None}
        self.db = Database(**self.sh_kwargs)

    def is_backend_task(self):
        return False

    def __get_uuids_from_profile_name(self, profile_name):
        """ Get the uuid for a profile name """
        uuids = []

        with self.db.connect() as session:
            query = session.query(Profile).\
            filter(Profile.name == profile_name)
            profiles = query.all()
            if profiles:
                for p in profiles:
                    uuids.append(p.uuid)
        return uuids

    def run(self):
        if self.unify:
            for algo in self.conf['sh_matching']:
                kwargs = {'matching':algo, 'fast_matching':True}
                logger.info("[sortinghat] Unifying identities using algorithm %s", kwargs['matching'])
                code = Unify(**self.sh_kwargs).unify(**kwargs)
                if code != CMD_SUCCESS:
                    logger.error("[sortinghat] Error in unify %s", kwargs)

        if self.affiliate:
            # Global enrollments using domains
            logger.info("[sortinghat] Executing affiliate")
            code = Affiliate(**self.sh_kwargs).affiliate()
            if code != CMD_SUCCESS:
                logger.error("[sortinghat] Error in affiliate %s", kwargs)


        if self.autoprofile:
            if not 'sh_autoprofile' in self.conf:
                logger.info("[sortinghat] Autoprofile not configured. Skipping.")
            else:
                logger.info("[sortinghat] Executing autoprofile: %s", self.conf['sh_autoprofile'])
                sources = self.conf['sh_autoprofile']
                code = AutoProfile(**self.sh_kwargs).autocomplete(sources)
                if code != CMD_SUCCESS:
                    logger.error("Error in autoprofile %s", kwargs)

        if self.bots:
            if not 'sh_bots_names' in self.conf:
                logger.info("[sortinghat] Bots name list not configured. Skipping.")
            else:
                logger.info("[sortinghat] Marking bots: %s",
                            self.conf['sh_bots_names'])
                for name in self.conf['sh_bots_names']:
                    # First we need the uuids for the profile name
                    uuids = self.__get_uuids_from_profile_name(name)
                    # Then we can modify the profile setting bot flag
                    profile = {"is_bot": True}
                    for uuid in uuids:
                        api.edit_profile(self.db, uuid, **profile)
                # For quitting the bot flag - debug feature
                if 'sh_no_bots_names' in self.conf:
                    logger.info("[sortinghat] Removing Marking bots: %s",
                                self.conf['sh_no_bots_names'])
                    for name in self.conf['sh_no_bots_names']:
                        uuids = self.__get_uuids_from_profile_name(name)
                        profile = {"is_bot": False}
                        for uuid in uuids:
                            api.edit_profile(self.db, uuid, **profile)


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
        menu_url = urljoin(self.conf['es_enrichment'] + "/", ".kibana/metadashboard/main")
        # r = requests.post(menu_url, data=json.dumps(dash_menu, sort_keys=True))
        r = requests.post(menu_url, data=json.dumps(dash_menu))
        r.raise_for_status()

    def __remove_dashboard_menu(self):
        """ The dashboard must be removed before creating a new one """
        logger.info("Remove dashboard menu definition")
        menu_url = urljoin(self.conf['es_enrichment'] + "/" , ".kibana/metadashboard/main")
        requests.delete(menu_url)

    def __get_menu_entries(self):
        """ Get the menu entries from the panel definition """
        menu_entries = OrderedDict()
        for entry in self.panels_menu:
            if entry['source'] not in self.data_sources:
                continue
            if 'kibana' in self.conf and self.conf['kibana'] == '5':
                menu_entries[entry['name']] = {}
            for subentry in entry['menu']:
                dash_name = get_dashboard_name(subentry['panel'])
                # The name for the entry is in self.panels_menu
                if 'kibana' in self.conf and self.conf['kibana'] == '5':
                    menu_entries[entry['name']][subentry['name']] = dash_name
                else:
                    menu_entries[dash_name] = dash_name

        return menu_entries

    def __get_dash_menu(self):
        """ Order the dashboard menu """
        # We need to get the current entries and add the new one
        current_menu = {}

        omenu = OrderedDict()
        if 'kibana' in self.conf and self.conf['kibana'] == '5':
            # Kibana5 menu version
            # First Main with Overview, Data Status and About
            omenu["Main"] = {"Overview": self.menu_panels_common['Overview']}
            omenu["Main"].update({"Data Status": self.menu_panels_common['Data Status']})
            omenu["Main"].update({"About": self.menu_panels_common['About']})
            ds_menu = self.__get_menu_entries()
            omenu.update(ds_menu)
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

    def run(self):
        # Create the panels menu
        menu = self.__get_dash_menu()
        # Remove the current menu and create the new one
        self.__remove_dashboard_menu()
        self.__create_dashboard_menu(menu)


class TaskPanels(Task):
    """ Create the panels  """

    panels_common = ["panels/dashboards/overview.json",
                     "panels/dashboards/about.json",
                     "panels/dashboards/data-status.json"]

    # aliases not following the ds-dev and ds rule
    aliases = {
        "bugzillarest": {
            "raw":["bugzilla-dev"],
            "enrich":["bugzilla"]
        },
        "git": {
            "raw":["git-dev"],
            "enrich":["git", "git_author", "git_enrich"]
        },
        "github": {
            "raw":["github-dev"],
            "enrich":["github_issues", "github_issues_enrich", "issues_closed",
                      "issues_created", "issues_updated"]
        },
        "jenkins": {
            "raw":["jenkins-dev"],
            "enrich":["jenkins", "jenkins_enrich"]
        },
        "mbox": {
            "raw":["mbox-dev"],
            "enrich":["mbox", "mbox_enrich"]
        },
        "pipermail": {
            "raw":["pipermail-dev"],
            "enrich":["mbox", "mbox_enrich"]
        },
        "phabricator": {
            "raw":["phabricator-dev"],
            "enrich":["phabricator", "maniphest"]
        },
        "remo": {
            "raw":["remo-dev"],
            "enrich":["remo", "remo2-events"]
        },
        "stackexchange": {
            "raw":["stackexchange-dev"],
            "enrich":["stackoverflow"]
        },
        "supybot": {
            "raw":["irc-dev"],
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
        ds = self.backend_name
        es_col_url = self._get_collection_url()
        es_enrich_url = self.conf['es_enrichment']

        index_raw = self.conf[ds]['raw_index']
        index_enrich = self.conf[ds]['enriched_index']

        if ds in self.aliases and 'raw' in self.aliases[ds]:
            for alias in self.aliases[ds]['raw']:
                self.__create_alias(es_col_url, index_raw, alias)
        else:
            # Standard alias for the raw index
            self.__create_alias(es_col_url, index_raw, ds+"-dev")

        if ds in self.aliases and 'enrich' in self.aliases[ds]:
            for alias in self.aliases[ds]['enrich']:
                self.__create_alias(es_enrich_url, index_enrich, alias)
        else:
            # Standard alias for the enrich index
            self.__create_alias(es_enrich_url, index_enrich, ds)


    def run(self):
        # Create the aliases
        self.__create_aliases()
        # Create the commons panels
        # TODO: do it only one time, not for every backend
        for panel_file in self.panels_common:
            import_dashboard(self.conf['es_enrichment'], panel_file)
        # Create the panels which uses the aliases as data source
        for panel_file in self.panels[self.backend_name]:
            import_dashboard(self.conf['es_enrichment'], panel_file)

class TaskRawDataCollection(Task):
    """ Basic class shared by all collection tasks """

    def __init__(self, conf, repos=None, backend_name=None):
        super().__init__(conf)
        self.repos = repos
        self.backend_name = backend_name
        # This will be options in next iteration
        self.clean = False

    def run(self):
        cfg = self.conf

        if 'collect' in cfg[self.backend_name] and \
            cfg[self.backend_name]['collect'] == False:
            logging.info('%s collect disabled', self.backend_name)
            return

        t2 = time.time()
        logger.info('[%s] raw data collection starts', self.backend_name)
        clean = False

        fetch_cache = False
        if 'fetch-cache' in self.conf[self.backend_name] and \
            self.conf[self.backend_name]['fetch-cache']:
            fetch_cache = True

        for repo in self.repos:
            p2o_args = self.compose_p2o_params(self.backend_name, repo)
            filter_raw = p2o_args['filter-raw'] if 'filter-raw' in p2o_args else None
            if filter_raw:
                # If filter-raw exists the goal is to enrich already collected
                # data, so don't collect anything
                logging.warning("Not collecting filter raw repository: %s", repo)
                continue
            url = p2o_args['url']
            backend_args = self.compose_perceval_params(self.backend_name, repo)
            logger.debug(backend_args)
            logger.debug('[%s] collection starts for %s', self.backend_name, repo)
            es_col_url = self._get_collection_url()
            ds = self.backend_name
            feed_backend(es_col_url, clean, fetch_cache, ds, backend_args,
                         cfg[ds]['raw_index'], cfg[ds]['enriched_index'], url)
        t3 = time.time()
        spent_time = time.strftime("%H:%M:%S", time.gmtime(t3-t2))
        logger.info('[%s] Data collection finished in %s',
                    self.backend_name, spent_time)

class TaskEnrich(Task):
    """ Basic class shared by all enriching tasks """

    def __init__(self, conf, repos=None, backend_name=None):
        super().__init__(conf)
        self.repos = repos
        self.backend_name = backend_name
        # This will be options in next iteration
        self.clean = False

    def __enrich_items(self):
        time_start = time.time()

        #logger.info('%s starts for %s ', 'enrichment', self.backend_name)
        logger.info('[%s] enrichment starts', self.backend_name)

        cfg = self.conf

        no_incremental = False
        github_token = None
        if 'github' in self.conf and 'backend_token' in self.conf['github']:
            github_token = self.conf['github']['backend_token']
        only_studies = False
        only_identities=False
        for repo in self.repos:
            # First process p2o params from repo
            p2o_args = self.compose_p2o_params(self.backend_name, repo)
            filter_raw = p2o_args['filter-raw'] if 'filter-raw' in p2o_args else None
            url = p2o_args['url']
            # Second process perceval params from repo
            backend_args = self.compose_perceval_params(self.backend_name, url)

            try:
                es_col_url = self._get_collection_url()
                logger.debug('[%s] enrichment starts for %s', self.backend_name, repo)
                enrich_backend(es_col_url, self.clean, self.backend_name,
                                backend_args,
                                cfg[self.backend_name]['raw_index'],
                                cfg[self.backend_name]['enriched_index'],
                                None, #projects_db is deprecated
                                cfg['projects_file'],
                                cfg['sh_database'],
                                no_incremental, only_identities,
                                github_token,
                                False, # studies are executed in its own Task
                                only_studies,
                                cfg['es_enrichment'],
                                None, #args.events_enrich
                                cfg['sh_user'],
                                cfg['sh_password'],
                                cfg['sh_host'],
                                None, #args.refresh_projects,
                                None, #args.refresh_identities,
                                author_id=None,
                                author_uuid=None,
                                filter_raw=filter_raw)
            except KeyError as e:
                logger.exception(e)

        time.sleep(5)  # Safety sleep tp avoid too quick execution

        spent_time = time.strftime("%H:%M:%S", time.gmtime(time.time()-time_start))
        logger.info('[%s] enrichment finished in %s', self.backend_name, spent_time)

    def __autorefresh(self):
        logging.info("[%s] Refreshing project and identities " + \
                     "fields for all items", self.backend_name)
        # Refresh projects
        if False:
            # TODO: Waiting that the project info is loaded from yaml files
            logging.info("Refreshing project field in enriched index")
            enrich_backend = self.get_enrich_backend()
            field_id = enrich_backend.get_field_unique_id()
            eitems = refresh_projects(enrich_backend)
            enrich_backend.elastic.bulk_upload_sync(eitems, field_id)

        # Refresh identities
        logging.info("Refreshing identities fields in enriched index")
        enrich_backend = self.get_enrich_backend()
        field_id = enrich_backend.get_field_unique_id()
        eitems = refresh_identities(enrich_backend)
        enrich_backend.elastic.bulk_upload_sync(eitems, field_id)

    def __studies(self):
        logging.info("Executing %s studies ...", self.backend_name)
        enrich_backend = self.get_enrich_backend()
        do_studies(enrich_backend)

    def run(self):
        if 'enrich' in self.conf[self.backend_name] and \
            self.conf[self.backend_name]['enrich'] == False:
            logging.info('%s enrich disabled', self.backend_name)
            return

        self.__enrich_items()
        if self.conf['autorefresh_on']:
            self.__autorefresh()
        if self.conf['studies_on']:
            self.__studies()


class TasksManager(threading.Thread):
    """
    Class to manage tasks execution

    All tasks in the same task manager will be executed in the same thread
    in a serial way.

    """

    def __init__(self, tasks_cls, backend_name, repos, stopper, conf, timer = 0):
        """
        :tasks_cls : tasks classes to be executed using the backend
        :backend_name: perceval backend name
        :repos: list of repositories to be managed
        :conf: conf for the manager
        """
        super().__init__()  # init the Thread
        self.conf = conf
        self.tasks_cls = tasks_cls  # tasks classes to be executed
        self.tasks = []  # tasks to be executed
        self.backend_name = backend_name
        self.repos = repos
        self.stopper = stopper  # To stop the thread from parent
        self.timer = timer

    def add_task(self, task):
        self.tasks.append(task)

    def run(self):
        logger.debug('Starting Task Manager thread %s', self.backend_name)

        # Configure the tasks
        logger.debug(self.tasks_cls)
        for tc in self.tasks_cls:
            # create the real Task from the class
            task = tc(self.conf)
            task.set_repos(self.repos)
            task.set_backend_name(self.backend_name)
            self.tasks.append(task)

        if not self.tasks:
            logger.debug('Task Manager thread %s without tasks', self.backend_name)

        logger.debug('run(tasks) - run(%s)' % (self.tasks))
        while not self.stopper.is_set():
            # we give 1 extra second to the stopper, so this loop does
            # not finish before it is set.
            time.sleep(1)

            if self.timer > 0:
                time.sleep(self.timer)

            for task in self.tasks:
                task.run()

        logger.debug('Exiting Task Manager thread %s', self.backend_name)


class ElasticSearchError(Exception):
    """Exception raised for errors in the list of backends
    """
    def __init__(self, expression):
        self.expression = expression

class Mordred:

    def __init__(self, conf_file):
        self.conf_file = conf_file
        self.conf = None

    def update_conf(self, conf):
        self.conf = conf

    def read_conf_files(self):
        conf = {}

        logger.debug("Reading conf files")
        config = configparser.ConfigParser()
        config.read(self.conf_file)
        logger.debug(config.sections())

        if 'min_update_delay' in config['general'].keys():
            conf['min_update_delay'] = config.getint('general','min_update_delay')
        else:
            # if no parameter is included, the update won't be performed more
            # than once every minute
            conf['min_update_delay'] = 60

        # FIXME: Read all options in a generic way
        conf['es_collection'] = config.get('es_collection', 'url')
        conf['es_enrichment'] = config.get('es_enrichment', 'url')
        conf['autorefresh_on'] = config.getboolean('es_enrichment', 'autorefresh')
        conf['studies_on'] = config.getboolean('es_enrichment', 'studies')

        projects_file = config.get('projects','projects_file')
        conf['projects_file'] = projects_file
        with open(projects_file,'r') as fd:
            projects = json.load(fd)
        conf['projects'] = projects

        conf['collection_on'] = config.getboolean('phases','collection')
        conf['identities_on'] = config.getboolean('phases','identities')
        conf['enrichment_on'] = config.getboolean('phases','enrichment')
        conf['panels_on'] = config.getboolean('phases','panels')

        conf['update'] = config.getboolean('general','update')
        try:
            conf['kibana'] = config.get('general','kibana')
        except configparser.NoOptionError:
            pass

        conf['sh_bots_names'] = config.get('sortinghat', 'bots_names').split(',')
        # Optional config params
        try:
            conf['sh_no_bots_names'] = config.get('sortinghat', 'no_bots_names').split(',')
        except configparser.NoOptionError:
            pass
        conf['sh_database'] = config.get('sortinghat', 'database')
        conf['sh_host'] = config.get('sortinghat', 'host')
        conf['sh_user'] = config.get('sortinghat', 'user')
        conf['sh_password'] = config.get('sortinghat', 'password')
        aux_matching = config.get('sortinghat', 'matching')
        conf['sh_matching'] = aux_matching.replace(' ','').split(',')
        aux_autoprofile = config.get('sortinghat', 'autoprofile')
        conf['sh_autoprofile'] = aux_autoprofile.replace(' ','').split(',')
        conf['sh_orgs_file'] = config.get('sortinghat', 'orgs_file')
        conf['sh_load_orgs'] = config.getboolean('sortinghat', 'load_orgs')

        try:
            conf['sh_sleep_for'] = config.getint('sortinghat','sleep_for')
        except configparser.NoOptionError:
            if conf['identities_on'] and conf['update']:
                logging.error(SLEEPFOR_ERROR)
            sys.exit(1)

        try:
            conf['sh_ids_file'] = config.get('sortinghat', 'identities_file')
        except configparser.NoOptionError:
            logger.info("No identities files")


        for backend in self.__get_backends():
            try:
                raw = config.get(backend, 'raw_index')
                enriched = config.get(backend, 'enriched_index')
                conf[backend] = {'raw_index':raw, 'enriched_index':enriched}
                for p in config[backend]:
                    try:
                        conf[backend][p] = config.getboolean(backend, p)
                    except ValueError:
                        conf[backend][p] = config.get(backend, p)
            except configparser.NoSectionError:
                pass

        return conf

    def check_es_access(self):
        ##
        ## So far there is no way to distinguish between read and write permission
        ##

        def _ofuscate_server_uri(uri):
            if uri.rfind('@') > 0:
                pre, post = uri.split('@')
                char_from = pre.rfind(':')
                result = uri[0:char_from + 1] + '****@' + post
                return result
            else:
                return uri

        es = self.conf['es_collection']
        try:
            r = requests.get(es, verify=False)
            if r.status_code != 200:
                raise ElasticSearchError(ES_ERROR % {'uri' : _ofuscate_server_uri(es)})
        except:
            raise ElasticSearchError(ES_ERROR % {'uri' : _ofuscate_server_uri(es)})


        if self.conf['enrichment_on'] or self.conf['studies_on']:
            es = self.conf['es_enrichment']
            try:
                r = requests.get(es, verify=False)
                if r.status_code != 200:
                    raise ElasticSearchError(ES_ERROR % {'uri' : _ofuscate_server_uri(es)})
            except:
                raise ElasticSearchError(ES_ERROR % {'uri' : _ofuscate_server_uri(es)})


    def __get_backends(self):
        gelk_backends = list(get_connectors().keys())
        extra_backends = ["google_hits"]

        return gelk_backends + extra_backends

    def __get_repos_by_backend(self):
        #
        # return dict with backend and list of repositories
        #
        output = {}
        projects = self.conf['projects']

        for backend in self.__get_backends():
            for pro in projects:
                if backend in projects[pro]:
                    if not backend in output:
                        output[backend]  = projects[pro][backend]
                    else:
                        output[backend] = output[backend] + projects[pro][backend]

        # backend could be in project/repo file but not enabled in
        # mordred conf file
        enabled = {}
        for k in output:
            if k in self.conf:
                enabled[k] = output[k]

        # logger.debug('repos to be retrieved: %s ', enabled)
        return enabled

    def execute_tasks (self, tasks_cls):
        """
            Just a wrapper to the execute_batch_tasks method
        """
        self.execute_batch_tasks(tasks_cls)

    def execute_nonstop_tasks(self, tasks_cls):
        """
            Just a wrapper to the execute_batch_tasks method
        """
        self.execute_batch_tasks(tasks_cls, self.conf['sh_sleep_for'], self.conf['min_update_delay'], False)

    def execute_batch_tasks(self, tasks_cls, big_delay=0, small_delay=0, wait_for_threads = True):
        """
        Start a task manager per backend to complete the tasks.

        :param task_cls: list of tasks classes to be executed
        :param big_delay: seconds before global tasks are executed, should be days usually
        :param small_delay: seconds before blackend tasks are executed, should be minutes
        :param wait_for_threads: boolean to set when threads are infinite or
                                should be synchronized in a meeting point
        """

        def _split_tasks(tasks_cls):
            """
            we internally distinguish between tasks executed by backend
            and tasks executed with no specific backend. """
            backend_t = []
            global_t = []
            for t in tasks_cls:
                if t.is_backend_task(t):
                    backend_t.append(t)
                else:
                    global_t.append(t)
            return backend_t, global_t

        logger.debug(' Task Manager starting .. ')

        backend_tasks, global_tasks = _split_tasks(tasks_cls)
        logger.debug ('backend_tasks = %s' % (backend_tasks))
        logger.debug ('global_tasks = %s' % (global_tasks))

        threads = []

        # stopper won't be set unless wait_for_threads is True
        stopper = threading.Event()

        # launching threads for tasks by backend
        if len(backend_tasks) > 0:
            repos_backend = self.__get_repos_by_backend()
            for backend in repos_backend:
                # Start new Threads and add them to the threads list to complete
                t = TasksManager(backend_tasks, backend, repos_backend[backend],
                                 stopper, self.conf, small_delay)
                threads.append(t)
                t.start()

        # launch thread for global tasks
        if len(global_tasks) > 0:
            #FIXME timer is applied to all global_tasks, does it make sense?
            gt = TasksManager(global_tasks, None, None, stopper, self.conf, big_delay)
            threads.append(gt)
            gt.start()
            if big_delay > 0:
                when = datetime.now() + timedelta(seconds = big_delay)
                when_str = when.strftime('%a, %d %b %Y %H:%M:%S %Z')
                logger.info("%s will be executed on %s" % (global_tasks, when_str))

        if wait_for_threads:
            time.sleep(1)  # Give enough time create and run all threads
            stopper.set()  # All threads must stop in the next iteration
            logger.debug(" Waiting for all threads to complete. This could take a while ..")

        # Wait for all threads to complete
        for t in threads:
            t.join()

        logger.debug(" Task manager and all its tasks (threads) finished!")

    def run(self):

        #logger.debug("Starting Mordred engine ...")
        logger.info("")
        logger.info("----------------------------")
        logger.info("Starting Mordred engine ...")
        logger.info("- - - - - - - - - - - - - - ")

        self.update_conf(self.read_conf_files())

        # check we have access to the needed ES
        self.check_es_access()

        # do we need ad-hoc scripts?

        tasks_cls = []
        all_tasks_cls = []

        # phase one
        # we get all the items with Perceval + identites browsing the
        # raw items

        if self.conf['identities_on']:
            tasks_cls = [TaskIdentitiesInit]
            self.execute_tasks(tasks_cls)

        if self.conf['collection_on']:
            tasks_cls = [TaskRawDataCollection]
            #self.execute_tasks(tasks_cls)
            if self.conf['identities_on']:
                tasks_cls.append(TaskIdentitiesCollection)
            all_tasks_cls += tasks_cls
            self.execute_tasks(tasks_cls)

        if self.conf['identities_on']:
            tasks_cls = [TaskIdentitiesMerge]
            all_tasks_cls += tasks_cls
            self.execute_tasks(tasks_cls)

        if self.conf['enrichment_on']:
            # raw items + sh database with merged identities + affiliations
            # will used to produce a enriched index
            tasks_cls = [TaskEnrich]
            all_tasks_cls += tasks_cls
            self.execute_tasks(tasks_cls)

        if self.conf['panels_on']:
            # Remove first the dashboard menu
            tasks_cls = [TaskPanels, TaskPanelsMenu]
            self.execute_tasks(tasks_cls)

        logger.debug(' - - ')
        logger.debug('Meeting point 0 reached')
        time.sleep(1)

        while self.conf['update']:
            self.execute_nonstop_tasks(all_tasks_cls)

        logger.info("Finished Mordred engine ...")
