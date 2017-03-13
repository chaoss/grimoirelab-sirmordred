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

import logging
import queue
import requests
import threading
import time
import traceback

from datetime import datetime, timedelta

from mordred.config import Config
from mordred.error import ElasticSearchError
from mordred.error import DataCollectionError
from mordred.error import DataEnrichmentError
from mordred.task import Task
from mordred.task_collection import TaskRawDataCollection
from mordred.task_enrich import TaskEnrich
from mordred.task_identities import TaskIdentitiesCollection, TaskIdentitiesInit, TaskIdentitiesMerge
from mordred.task_manager import TasksManager
from mordred.task_panels import TaskPanels, TaskPanelsMenu


ES_ERROR = "Before starting to seek the Holy Grail, make sure your ElasticSearch " + \
"at '%(uri)s' is available!!\n - Mordred said."


logger = logging.getLogger(__name__)



class Mordred:

    def __init__(self, conf_file):
        self.conf = Config(conf_file).get_conf()

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

        es = self.conf['es_collection']['url']
        try:
            r = requests.get(es, verify=False)
            if r.status_code != 200:
                raise ElasticSearchError(ES_ERROR % {'uri' : _ofuscate_server_uri(es)})
        except:
            raise ElasticSearchError(ES_ERROR % {'uri' : _ofuscate_server_uri(es)})


        if self.conf['phases']['enrichment'] or \
           self.conf['es_enrichment']['studies']:
            es = self.conf['es_enrichment']['url']
            try:
                r = requests.get(es, verify=False)
                if r.status_code != 200:
                    raise ElasticSearchError(ES_ERROR % {'uri' : _ofuscate_server_uri(es)})
            except:
                raise ElasticSearchError(ES_ERROR % {'uri' : _ofuscate_server_uri(es)})


    def _get_repos_by_backend(self):
        #
        # return dict with backend and list of repositories
        #
        output = {}
        projects = self.conf['projects_data']

        for backend_section in Config.get_backend_sections():
            for pro in projects:
                backend = Task.get_backend(backend_section)
                if backend in projects[pro]:
                    if not backend_section in output:
                        output[backend_section]  = projects[pro][backend]
                    else:
                        output[backend_section] += projects[pro][backend]

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
        self.execute_batch_tasks(tasks_cls,
                                 self.conf['sortinghat']['sleep_for'],
                                 self.conf['general']['min_update_delay'], False)

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

        logger.debug('Tasks Manager starting .. ')

        backend_tasks, global_tasks = _split_tasks(tasks_cls)
        logger.debug ('backend_tasks = %s' % (backend_tasks))
        logger.debug ('global_tasks = %s' % (global_tasks))

        threads = []

        # stopper won't be set unless wait_for_threads is True
        stopper = threading.Event()

        # launching threads for tasks by backend
        if len(backend_tasks) > 0:
            repos_backend = self._get_repos_by_backend()
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

        # Checking for exceptions in threads to log them
        self.__check_queue_for_errors()

        logger.debug(" Task manager and all its tasks (threads) finished!")

    def __check_queue_for_errors(self):
        try:
            exc = TasksManager.COMM_QUEUE.get(block=False)
        except queue.Empty:
            logger.debug("No exceptions in threads. Let's continue ..")
        else:
            exc_type, exc_obj, exc_trace = exc
            # deal with the exception
            logger.error(exc_type)
            raise exc_obj

    def run(self):
        """
        This method defines the workflow of Mordred. So it calls to:
        - initialize the databases
        - execute the different phases for the first iteration
          (collection, identities, enrichment)
        - start the collection and enrichment in parallel by data source
        - start also the Sorting Hat merge
        """

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

        if self.conf['phases']['identities']:
            tasks_cls = [TaskIdentitiesInit]
            self.execute_tasks(tasks_cls)

        # handling the exception below and continuing the execution is
        # a bit unstable, we could have several threads collecting data
        # and one of them crash, where this behaviour is ok. But we also
        # could have all of them crashed and this piece of code should
        # be smart enough to stop the execution. #FIXME
        try:
            if self.conf['phases']['collection']:
                tasks_cls = [TaskRawDataCollection]
                if self.conf['phases']['identities']:
                    tasks_cls.append(TaskIdentitiesCollection)
                all_tasks_cls += tasks_cls
                self.execute_tasks(tasks_cls)

        except DataCollectionError as e:
            logger.error(str(e))
            var = traceback.format_exc()
            logger.error(var)

        if self.conf['phases']['identities']:
            tasks_cls = [TaskIdentitiesMerge]
            all_tasks_cls += tasks_cls
            self.execute_tasks(tasks_cls)

        # handling this exception adds the same issue as above with the
        # exception for DataCollectionError. So this is another #FIXME
        try:
            if self.conf['phases']['enrichment']:
                # raw items + sh database with merged identities + affiliations
                # will used to produce a enriched index
                tasks_cls = [TaskEnrich]
                all_tasks_cls += tasks_cls
                self.execute_tasks(tasks_cls)

        except DataEnrichmentError as e:
            logger.error(str(e))
            var = traceback.format_exc()
            logger.error(var)

        if self.conf['phases']['panels']:
            tasks_cls = [TaskPanels, TaskPanelsMenu]
            self.execute_tasks(tasks_cls)

        logger.debug(' - - ')
        logger.debug('Meeting point 0 reached')
        time.sleep(1)

        # this is the main loop, where the execution should spend
        # most of its time
        while self.conf['general']['update']:
            try:
                self.execute_nonstop_tasks(all_tasks_cls)

                #FIXME this point is never reached so despite the exception is
                #handled and the error is shown, the traceback is not printed

            except DataCollectionError as e:
                logger.error(str(e))
                var = traceback.format_exc()
                logger.error(var)
                pass
            except DataEnrichmentError as e:
                logger.error(str(e))
                var = traceback.format_exc()
                logger.error(var)
                pass

        logger.info("Finished Mordred engine ...")
