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
import argparse
import time
import threading
import json
import sys
import requests
import random

from urllib.parse import urljoin

from grimoire.arthur import (feed_backend, enrich_backend, get_ocean_backend,
                             load_identities, do_studies,
                             refresh_projects, refresh_identities)
from grimoire.panels import import_dashboard
from grimoire.utils import get_connectors, get_connector_from_name, get_elastic

from sortinghat import api

from sortinghat.cmd.affiliate import Affiliate
from sortinghat.cmd.autoprofile import AutoProfile
from sortinghat.cmd.init import Init
from sortinghat.cmd.load import Load
from sortinghat.cmd.organizations import Organizations
from sortinghat.cmd.unify import Unify


from sortinghat.command import CMD_SUCCESS

SLEEPFOR_ERROR = """Error: You may be Arthur, King of the Britons. But you still """ + \
"""need the 'sleep_for' variable in sortinghat section\n - Mordred said."""
ES_ERROR = "Before starting to seek the Holy Grail, make sure your ElasticSearch " + \
"at '%(uri)s' is available!!\n - Mordred said."

logger = logging.getLogger(__name__)

class Task():
    """ Basic class shared by all tasks """

    def __init__(self, conf):
        self.conf = conf
        self.db_sh = self.conf['sh_database']
        self.db_user = self.conf['sh_user']
        self.db_password = self.conf['sh_password']
        self.db_host = self.conf['sh_host']

    def __get_github_owner_repo(self, github_url):
        owner = github_url.split('/')[-2]
        repo = github_url.split('/')[-1]
        return (owner, repo)

    def compose_perceval_params(self, backend_name, repo):
        params = []
        if backend_name == 'git':
            params.append(str(repo))
        elif backend_name == 'github':
            owner, github_repo = self.__get_github_owner_repo(repo)
            params.append('--owner')
            params.append(owner)
            params.append('--repository')
            params.append(github_repo)
            params.append('--sleep-for-rate')
            params.append('-t')
            params.append(self.conf['github']['token'])
        elif backend_name == 'stackexchange':
            tokens = repo.replace('https://','').replace('http://','').split('/')
            tag = tokens[-1]
            site = tokens[0]
            params.append('--site')
            params.append(site)
            params.append('--tagged')
            params.append(tag)
            params.append('--tag') #this is the origin we record in our DB
            params.append(repo)
            params.append('--token')
            params.append(self.conf['stackexchange']['token'])
        return params

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
        'token' in self.conf['github'].keys() and\
         self.backend_name == "git":
            gh_token = self.conf['github']['token']
            enrich_backend.set_github_token(gh_token)

        return enrich_backend

    def get_ocean_backend(self, enrich_backend):
        backend_cmd = None  # FIXME: Could we build a backend_cmd with params?

        no_incremental = False
        clean = False

        ocean_backend = get_ocean_backend(backend_cmd, enrich_backend, no_incremental)
        elastic_ocean = get_elastic(self.conf['es_collection'],
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
            ocean_backend = self.get_ocean_backend(enrich_backend)
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


class TaskIdentitiesMerge(Task):
    """ Basic class shared by all Sorting Hat tasks """

    def __init__(self, conf, load_orgs=True, load_ids=True, unify=True,
                 autoprofile=True, affiliate=True):
        super().__init__(conf)

        self.load_ids = load_ids  # Load identities from raw index
        self.unify = unify  # Unify identities
        self.autoprofile = autoprofile  # Execute autoprofile
        self.affiliate = affiliate # Affiliate identities
        self.sh_kwargs={'user': self.db_user, 'password': self.db_password,
                        'database': self.db_sh, 'host': self.db_host,
                        'port': None}

    def is_backend_task(self):
        return False

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
            logger.info("[sortinghat] Executing autoprofile: %s", self.conf['sh_autoprofile'])
            if not 'sh_autoprofile' in self.conf:
                logger.info("[sortinghat] Autoprofile not configured. Skipping.")
            else:
                sources = self.conf['sh_autoprofile']
                code = AutoProfile(**self.sh_kwargs).autocomplete(sources)
                if code != CMD_SUCCESS:
                    logger.error("Error in autoprofile %s", kwargs)


class TaskPanels(Task):
    """ Create the panels  """

    panels = {
        "git": ["panels/dashboards/git-organizations-projects.json",
                "panels/dashboards/git_demographics-organizations-projects.json"
                ],
        "github": ["panels/dashboards/github_backlog_organizations.json",
                   "panels/dashboards/github_issues-organizations.json",
                   "panels/dashboards/github_pullrequests_delays-organizations.json",
                   "panels/dashboards/github_pullrequests-organizations.json"
                   ]
    }

    aliases = {
        "git": {
            "raw":["git-dev"],
            "enrich":["git", "git_author", "git_enrich"]
        },
        "github": {
            "raw":["github-dev"],
            "enrich":["github_issues", "github_issues_enrich", "issues_closed",
                      "issues_created", "issues_updated"]
        }
    }

    dash_menu = """
    {
        "Overview": "Overview",
        "Git": "Git",
        "Issues": "GitHub-Issues",
        "Pull Requests": "Github-Pull-Requests",
        "Github Backlog": "Github-Backlog",
        "PR Delays": "GitHub-Pull-Requests-Delays",
        "Demographics": "Git-Demographics",
        "Data Status": "Data-Status",
        "About": "About"
    }
    """

    def __remove_alias(self, es_url, alias):
        alias_url = urljoin(es_url, "_alias/"+alias)
        r = requests.get(alias_url)
        if r.status_code == 200:
            # The alias exists, let's remove it
            real_index = list(r.json())[0]
            logger.debug("Removing alias %s to %s", alias, real_index)
            aliases_url = urljoin(es_url, "_aliases")
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
        alias_url = urljoin(es_url, "_aliases")
        action = """
        {
            "actions" : [
                {"add" : { "index" : "%s",
                           "alias" : "%s" }}
           ]
         }
        """ % (es_index, alias)

        r = requests.post(alias_url, data=action)
        r.raise_for_status()

    def __create_aliases(self):
        """ Create aliases in ElasticSearch used by the panels """
        es_col_url = self.conf['es_collection']
        es_enrich_url = self.conf['es_enrichment']

        ds = self.backend_name
        index_raw = self.conf[ds]['raw_index']
        index_enrich = self.conf[ds]['enriched_index']

        if 'raw' in self.aliases[ds]:
            for alias in self.aliases[ds]['raw']:
                self.__create_alias(es_col_url, index_raw, alias)
        else:
            # Standard alias for the raw index
            self.__create_alias(es_col_url, index_raw, ds+"-dev")

        if 'enrich' in self.aliases[ds]:
            for alias in self.aliases[ds]['enrich']:
                self.__create_alias(es_enrich_url, index_enrich, alias)
        else:
            # Standard alias for the enrich index
            self.__create_alias(es_enrich_url, index_enrich, ds)

    def __create_dashboard_menu(self, es_url, dash_menu):
        """ Create the menu definition to access the panels in a dashboard """
        # TODO: only the menu for the self.backend_name should be added
        # TODO: but howto add the global menu entries and define the order
        logger.info("Adding dashboard menu definition")
        alias_url = urljoin(es_url, ".kibana/metadashboard/main")
        r = requests.post(alias_url, data=dash_menu)
        r.raise_for_status()

    def run(self):
        # Create the aliases
        self.__create_aliases()
        # Create the panels which uses the aliases as data source
        for panel_file in self.panels[self.backend_name]:
            import_dashboard(self.conf['es_enrichment'], panel_file)
        # Create the menu for accessing the dashboards
        self.__create_dashboard_menu(self.conf['es_enrichment'], self.dash_menu)


class TaskRawDataCollection(Task):
    """ Basic class shared by all collection tasks """

    def __init__(self, conf, repos=None, backend_name=None):
        super().__init__(conf)
        self.repos = repos
        self.backend_name = backend_name
        # This will be options in next iteration
        self.clean = False
        self.fetch_cache = False

    def run(self):
        t2 = time.time()
        logger.info('[%s] raw data collection starts', self.backend_name)
        clean = False
        fetch_cache = False
        cfg = self.conf
        for r in self.repos:
            backend_args = self.compose_perceval_params(self.backend_name, r)
            logger.debug('[%s] collection starts for %s', self.backend_name, r)
            feed_backend(cfg['es_collection'], clean, fetch_cache,
                        self.backend_name,
                        backend_args,
                        cfg[self.backend_name]['raw_index'],
                        cfg[self.backend_name]['enriched_index'],
                        r)

        time.sleep(random.randint(0,20)) # FIXME test purposes

        t3 = time.time()
        spent_time = time.strftime("%H:%M:%S", time.gmtime(t3-t2))
        logger.info('[%s] Data collection finished in %s' % (self.backend_name, spent_time))

class TaskEnrich(Task):
    """ Basic class shared by all enriching tasks """

    def __init__(self, conf, repos=None, backend_name=None):
        super().__init__(conf)
        self.repos = repos
        self.backend_name = backend_name
        # This will be options in next iteration
        self.clean = False
        self.fetch_cache = False

    def __enrich_items(self):
        time_start = time.time()

        #logger.info('%s starts for %s ', 'enrichment', self.backend_name)
        logger.info('[%s] enrichment starts', self.backend_name)

        cfg = self.conf

        no_incremental = False
        github_token = None
        if 'github' in self.conf and 'token' in self.conf['github']:
            github_token = self.conf['github']['token']
        only_studies = False
        only_identities=False
        for r in self.repos:
            backend_args = self.compose_perceval_params(self.backend_name, r)

            try:
                logger.debug('[%s] enrichment starts for %s', self.backend_name, r)
                enrich_backend(cfg['es_collection'], self.clean, self.backend_name,
                                backend_args, #FIXME #FIXME
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
                                None) #args.refresh_identities)
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

    def __init__(self, tasks_cls, backend_name, repos, stopper, conf):
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
        self.rounds_limit = 0  # For debugging

    def add_task(self, task):
        self.tasks.append(task)

    def run(self):
        logger.debug('Starting Task Manager thread %s', self.backend_name)

        # Configure the tasks
        for task_cls in self.tasks_cls:
            task = task_cls(self.conf)  # create the real Task from the class
            task.set_repos(self.repos)
            task.set_backend_name(self.backend_name)
            self.tasks.append(task)

        if not self.tasks:
            logger.debug('Task Manager thread %s without tasks', self.backend_name)

        rounds = 0

        while not self.stopper.is_set():
            for task in self.tasks:
                task.run()
            rounds  += 1
            if rounds > self.rounds_limit:
                break

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
        logger = self.setup_logs()

    def setup_logs(self):

        # For gelk logging
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')
        # To control requests logging
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)

        #logging.basicConfig(filename='mordred.log',level=logging.DEBUG)
        #logger = logging.getLogger('mordred')
        logger.setLevel(logging.INFO)

        fh = logging.FileHandler('spam.log')
        fh.setLevel(logging.DEBUG)
        # create console handler with a higher log level
        ch = logging.StreamHandler()
        ch.setLevel(logging.ERROR)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        fh.setFormatter(formatter)
        # add the handlers to logger
        logger.addHandler(ch)
        logger.addHandler(fh)
        #self.projects = None
        return logger

    def update_conf(self, conf):
        self.conf = conf

    def read_conf_files(self):
        conf = {}

        logger.debug("Reading conf files")
        config = configparser.ConfigParser()
        config.read(self.conf_file)
        logger.debug(config.sections())

        try:
            if 'sleep' in config['general'].keys():
                sleep = config.get('general','sleep')
            else:
                sleep = 0
            conf['sleep'] = sleep

        except KeyError:
            logger.error("'general' section is missing from %s " + \
                        "conf file", self.conf_file)

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
            conf['sh_sleep_for'] = config.get('sortinghat','sleep_for')
        except configparser.NoOptionError:
            if conf['identities_on'] and conf['update']:
                logging.error(SLEEPFOR_ERROR)
            sys.exit(1)

        for backend in get_connectors().keys():
            try:
                raw = config.get(backend, 'raw_index')
                enriched = config.get(backend, 'enriched_index')
                conf[backend] = {'raw_index':raw, 'enriched_index':enriched}
                if backend == 'github' or backend == 'stackexchange':
                    # FIXME
                    # token should be part of a secondary file
                    conf[backend]['token'] = config.get(backend, 'token')
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


    def feed_orgs_tables(self):
        print("Not implemented")

    def __get_repos_by_backend(self):
        #
        # return dict with backend and list of repositories
        #
        output = {}
        projects = self.conf['projects']

        for backend in get_connectors().keys():
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

    def collect_identities(self):
        self.data_enrichment(True)

    def data_enrichment_studies(self):
        logger.info("Not implemented")

    def update_es_aliases(self):
        logger.info("Not implemented")

    def identities_merge(self):
        logger.info("Not implemented")

    def execute_batch_tasks(self, tasks_cls, timer=0):
        """
        Start a task manger per backend to complete the tasks.

        All the tasks that should be executed according to the config
        must be added to the task manager.
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

        threads = []
        stopper = threading.Event()

        # launching threads for tasks by backend
        if len(backend_tasks) > 0:
            repos_backend = self.__get_repos_by_backend()
            for backend in repos_backend:
                # Start new Threads and add them to the threads list to complete
                t = TasksManager(tasks_cls, backend, repos_backend[backend],
                                 stopper, self.conf)
                threads.append(t)
                t.start()

        if timer:
            if self.conf['identities_on']:
                logger.info(" Identities merge will be executed in  %s seconds", str(timer))
            time.sleep(timer)

        # launch thread for global tasks
        if len(global_tasks) > 0:
            gt = TasksManager(global_tasks, None, None, stopper, self.conf)
            threads.append(gt)
            gt.start()

        stopper.set()

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

        # projects database, do we need to feed it?
        self.feed_orgs_tables()

        tasks_cls = []

        # phase one
        # we get all the items with Perceval + identites browsing the
        # raw items

        if self.conf['identities_on']:
            tasks_cls = [TaskIdentitiesInit]
            self.execute_batch_tasks(tasks_cls)

        if self.conf['collection_on']:
            tasks_cls = [TaskRawDataCollection]
            #self.execute_batch_tasks(tasks_cls)
            if self.conf['identities_on']:
                tasks_cls.append(TaskIdentitiesCollection)
            self.execute_batch_tasks(tasks_cls)

        if self.conf['identities_on']:
            tasks_cls = [TaskIdentitiesMerge]
            self.execute_batch_tasks(tasks_cls)

        if self.conf['enrichment_on']:
            # raw items + sh database with merged identities + affiliations
            # will used to produce a enriched index
            tasks_cls = [TaskEnrich]
            self.execute_batch_tasks(tasks_cls)

        if self.conf['panels_on']:
            tasks_cls = [TaskPanels]
            self.execute_batch_tasks(tasks_cls)

        while self.conf['update']:

            tasks_cls = [TaskRawDataCollection,
                         TaskIdentitiesCollection,
                         TaskIdentitiesMerge,
                         TaskEnrich]

            self.execute_batch_tasks(tasks_cls, self.conf['sh_sleep_for'])

            # FIXME
            # reached this point a new index should be produced
            # or the one we are using should be updated with the Changes
            # for unified identities + affiliations

            # do aliases need to be changed?
            self.update_es_aliases()

def parse_args():

    parser = argparse.ArgumentParser(
        description='Mordred, the friendly friend of p2o',
        epilog='Software metrics for your peace of mind'
        )

    parser.add_argument('-c','--config', help='Configuration file',
        required=True, dest='config_file')

    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = parse_args()
    obj = Mordred(args.config_file)
    try:
        obj.run()
    except ElasticSearchError as e:
        s = 'Error: %s\n' % str(e)
        sys.stderr.write(s)
        sys.exit(1)
