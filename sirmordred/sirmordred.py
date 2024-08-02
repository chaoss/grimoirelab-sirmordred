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
#     Quan Zhou <quan@bitergia.com>
#

import json
import logging
import queue
import sys
import threading
import time
import traceback

from datetime import datetime, timedelta

import requests

import warnings
warnings.filterwarnings("ignore", message="numpy.dtype size changed")
warnings.filterwarnings("ignore", message="numpy.ufunc size changed")

from grimoire_elk.enriched.utils import grimoire_con

from sirmordred.config import Config
from sirmordred.error import DataCollectionError
from sirmordred.error import DataEnrichmentError
from sirmordred.task_autorefresh import TaskAutorefresh
from sirmordred.task_collection import TaskRawDataCollection
from sirmordred.task_enrich import TaskEnrich
from sirmordred.task_identities import TaskIdentitiesMerge
from sirmordred.task_manager import TasksManager
from sirmordred.task_panels import TaskPanels, TaskPanelsMenu
from sirmordred.task_projects import TaskProjects
from sortinghat.cli.client import SortingHatClient

logger = logging.getLogger(__name__)


class SirMordred:

    def __init__(self, config):
        """ config is a Config object """
        self.config = config
        self.conf = config.get_conf()
        self.grimoire_con = grimoire_con(conn_retries=12)  # 30m retry

    def check_bestiary_access(self):

        bestiary_access = False

        bestiary_url = self.conf['projects']['projects_url']
        try:
            res = requests.get(bestiary_url)
            res.raise_for_status()
            res.json()
            bestiary_access = True
        except requests.exceptions.ConnectionError as ex:
            logging.error("Can not connect to bestiary %s", bestiary_url)
        except requests.exceptions.HTTPError as ex:
            logging.error("Can not get projects for %s", bestiary_url)
        except json.decoder.JSONDecodeError:
            res_line = res.text.split('\n', 1)[0]
            logging.error("Can not parse JSON projects for %s: %s", bestiary_url, res_line)

        return bestiary_access

    def check_es_access(self):

        # So far there is no way to distinguish between read and write permission

        es_access = True
        es_error = None

        def _ofuscate_server_uri(uri):
            if uri.rfind('@') > 0:
                pre, post = uri.split('@')
                char_from = pre.rfind(':')
                result = uri[0:char_from + 1] + '****@' + post
                return result
            else:
                return uri

        es = self.conf['es_collection']['url']
        try:
            res = self.grimoire_con.get(es)
            res.raise_for_status()
        except Exception:
            es_access = False
            es_error = _ofuscate_server_uri(es)

        if self.conf['phases']['enrichment']:
            es = self.conf['es_enrichment']['url']
            try:
                res = self.grimoire_con.get(es)
                res.raise_for_status()
            except Exception:
                es_access = False
                es_error = _ofuscate_server_uri(es)

        if not es_access:
            logger.error('Cannot connect to Elasticsearch: %s', es_error)

        return es_access

    def _get_repos_by_backend(self):
        #
        # return dict with backend and list of repositories
        #
        output = {}
        projects = TaskProjects.get_projects()

        for pro in projects:
            # remove duplicates in backends_section with list(set(..))
            backend_sections = list(set([sect for sect in projects[pro].keys()
                                         for backend_section in Config.get_backend_sections()
                                         if sect and sect.startswith(backend_section)]))

            # sort backends section
            backend_sections.sort()
            for backend_section in backend_sections:
                if backend_section not in output:
                    output[backend_section] = projects[pro][backend_section]
                else:
                    output[backend_section] += projects[pro][backend_section]

        # backend could be in project/repo file but not enabled in
        # sirmordred conf file
        enabled = {}
        for k in output:
            if k in self.conf:
                enabled[k] = output[k]

        # logger.debug('repos to be retrieved: %s ', enabled)
        return enabled

    def execute_nonstop_tasks(self, tasks_cls):
        """
            Just a wrapper to the execute_batch_tasks method
        """
        sleep_for = self.conf['sortinghat']['sleep_for'] if self.conf.get('sortinghat', None) else 1
        self.execute_batch_tasks(tasks_cls,
                                 sleep_for,
                                 self.conf['general']['min_update_delay'], False)

    def execute_batch_tasks(self, tasks_cls, big_delay=0, small_delay=0, wait_for_threads=True):
        """
        Start a task manager per backend to complete the tasks.

        :param tasks_cls: list of tasks classes to be executed
        :param big_delay: seconds before global tasks are executed, should be days usually
        :param small_delay: seconds before backend tasks are executed, should be minutes
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

        backend_tasks, global_tasks = _split_tasks(tasks_cls)
        logger.debug('backend_tasks = %s' % (backend_tasks))
        logger.debug('global_tasks = %s' % (global_tasks))

        threads = []

        # stopper won't be set unless wait_for_threads is True
        stopper = threading.Event()

        # launching threads for tasks by backend
        if len(backend_tasks) > 0:
            repos_backend = self._get_repos_by_backend()
            for backend in repos_backend:
                # Start new Threads and add them to the threads list to complete
                t = TasksManager(backend_tasks, backend, stopper, self.config, self.client, small_delay)
                threads.append(t)
                t.start()

        # launch thread for global tasks
        if len(global_tasks) > 0:
            # FIXME timer is applied to all global_tasks, does it make sense?
            # All tasks are executed in the same thread sequentially
            gt = TasksManager(global_tasks, "Global tasks", stopper, self.config, self.client, big_delay)
            threads.append(gt)
            gt.start()
            if big_delay > 0:
                when = datetime.now() + timedelta(seconds=big_delay)
                when_str = when.strftime('%a, %d %b %Y %H:%M:%S %Z')
                logger.info("%s will be executed on %s" % (' '.join([g.__name__ for g in global_tasks]),
                                                           when_str))

        if wait_for_threads:
            time.sleep(1)  # Give enough time create and run all threads
            stopper.set()  # All threads must stop in the next iteration

        # Wait for all threads to complete
        for t in threads:
            t.join()

        # Checking for exceptions in threads to log them
        self.__check_queue_for_errors()

        logger.debug("[thread:main] All threads (and their tasks) are finished")

    def __check_queue_for_errors(self):
        try:
            exc = TasksManager.COMM_QUEUE.get(block=False)
        except queue.Empty:
            logger.debug("[thread:main] No exceptions in threads queue. Let's continue ..")
        else:
            exc_type, exc_obj, exc_trace = exc
            # deal with the exception
            logger.error(exc_type)
            raise exc_obj

    def __execute_initial_load(self):
        """
        Tasks that should be done just one time
        """
        stopper = threading.Event()

        if self.conf['phases']['panels']:
            tasks = [TaskPanels, TaskPanelsMenu]
            stopper.set()
            tm = TasksManager(tasks, "Global tasks", stopper, self.config, self.client)
            tm.start()
            tm.join()

        logger.info("Loading projects")
        tasks = [TaskProjects]
        stopper.set()
        tm = TasksManager(tasks, "Global tasks", stopper, self.config, self.client)
        tm.start()
        tm.join()
        logger.info("Projects loaded")

        return

    def start(self):
        """
        This method defines the workflow of SirMordred. So it calls to:
        - initialize the databases
        - execute the different phases for the first iteration
          (collection, identities, enrichment)
        - start the collection and enrichment in parallel by data source
        - start also the Sorting Hat merge
        """

        # logger.debug("Starting SirMordred engine ...")
        logger.info("")
        logger.info("----------------------------")
        logger.info("Starting SirMordred engine ...")
        logger.info("----------------------------")

        # check we have access to the needed ES
        if not self.check_es_access():
            print('Can not access ElasticSearch/OpenSearch service. Exiting sirmordred ...')
            sys.exit(1)

        # If bestiary is configured check that it is working
        if self.conf['projects']['projects_url']:
            if not self.check_bestiary_access():
                print('Can not access bestiary service. Exiting sirmordred ...')
                sys.exit(1)

        # Create SortingHat Client
        self.__create_sh_client(self.config)

        # Initial round: panels and projects loading
        self.__execute_initial_load()

        # Tasks to be executed during updating process
        all_tasks_cls = []
        all_tasks_cls.append(TaskProjects)  # projects update is always needed
        if self.conf['phases']['collection']:
            all_tasks_cls.append(TaskRawDataCollection)
        if self.conf['phases']['identities']:
            all_tasks_cls.append(TaskIdentitiesMerge)
        if self.conf['phases']['enrichment']:
            all_tasks_cls.append(TaskEnrich)
            all_tasks_cls.append(TaskAutorefresh)

        # this is the main loop, where the execution should spend
        # most of its time

        while True:

            if not all_tasks_cls:
                logger.warning("No tasks to execute.")
                break

            try:
                if not self.conf['general']['update']:
                    sleep_for = self.conf['sortinghat']['sleep_for'] if self.conf.get('sortinghat', None) else 1
                    self.execute_batch_tasks(all_tasks_cls,
                                             sleep_for,
                                             self.conf['general']['min_update_delay'])
                    break
                else:
                    self.execute_nonstop_tasks(all_tasks_cls)

                # FIXME this point is never reached so despite the exception is
                # handled and the error is shown, the traceback is not printed

            except DataCollectionError as e:
                logger.error(str(e))
                var = traceback.format_exc()
                logger.error(var)

            except DataEnrichmentError as e:
                logger.error(str(e))
                var = traceback.format_exc()
                logger.error(var)

        logger.info("Finished SirMordred engine ...")

    def __create_sh_client(self, config):
        self.config = config
        self.conf = config.get_conf()

        sortinghat = self.conf.get('sortinghat', None)
        self.db_sh = sortinghat['database'] if sortinghat else None
        self.db_user = sortinghat['user'] if sortinghat else None
        self.db_password = sortinghat['password'] if sortinghat else None
        self.db_host = sortinghat['host'] if sortinghat else '127.0.0.1'
        self.db_path = sortinghat.get('path', None) if sortinghat else None
        self.db_port = sortinghat.get('port', None) if sortinghat else None
        self.db_ssl = sortinghat.get('ssl', False) if sortinghat else False
        self.db_verify_ssl = sortinghat.get('verify_ssl', True) if sortinghat else True
        self.db_tenant = sortinghat.get('tenant', True) if sortinghat else None
        self.db_unaffiliate_group = sortinghat['unaffiliated_group'] if sortinghat else None
        if sortinghat and not hasattr(self, 'client'):
            self.client = SortingHatClient(host=self.db_host, port=self.db_port,
                                           path=self.db_path, ssl=self.db_ssl,
                                           user=self.db_user, password=self.db_password,
                                           verify_ssl=self.db_verify_ssl,
                                           tenant=self.db_tenant)
            self.client.connect()
        elif not sortinghat:
            self.client = None
