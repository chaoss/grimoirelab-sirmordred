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
import json
import sys
import requests
import threading

from datetime import datetime, timedelta

from grimoire_elk.utils import get_connectors

from mordred.task_collection import TaskRawDataCollection, TaskRawDataArthurCollection
from mordred.task_enrich import TaskEnrich
from mordred.task_identities import TaskIdentitiesCollection, TaskIdentitiesInit, TaskIdentitiesMerge
from mordred.task_manager import TasksManager
from mordred.task_panels import TaskPanels, TaskPanelsMenu

SLEEPFOR_ERROR = """Error: You may be Arthur, King of the Britons. But you still """ + \
"""need the 'sleep_for' variable in sortinghat section\n - Mordred said."""
ES_ERROR = "Before starting to seek the Holy Grail, make sure your ElasticSearch " + \
"at '%(uri)s' is available!!\n - Mordred said."

logger = logging.getLogger(__name__)

class ElasticSearchError(Exception):
    """Exception raised for errors in the list of backends
    """
    def __init__(self, expression):
        self.expression = expression

class Mordred:

    def __init__(self, conf_file):
        self.conf_file = conf_file
        self.conf = None
        self.conf = self.__read_conf_files()

    def __read_conf_files(self):
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
        conf['arthur_on'] = False
        if 'arthur' in config['es_collection'].keys():
            conf['arthur_on'] = config.getboolean('es_collection','arthur')
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
            if not self.conf['arthur_on']:
                tasks_cls = [TaskRawDataCollection]
            else:
                tasks_cls = [TaskRawDataArthurCollection]
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
