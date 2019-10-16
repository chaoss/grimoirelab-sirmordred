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

import logging
import queue
import threading
import sys
import time

logger = logging.getLogger(__name__)


class TasksManager(threading.Thread):
    """
    Class to manage tasks execution

    All tasks in the same task manager will be executed in the same thread
    in a serial way.

    """

    # this queue supports the communication from threads to mother process
    COMM_QUEUE = queue.Queue()
    # to control if enrichment process are active
    NUMBER_ENRICH_TASKS_ON_LOCK = threading.Lock()
    NUMBER_ENRICH_TASKS_ON = 0
    # to control if identities process are active
    IDENTITIES_TASKS_ON_LOCK = threading.Lock()
    IDENTITIES_TASKS_ON = False

    def __init__(self, tasks_cls, backend_section, stopper, config, timer=0):
        """
        :tasks_cls : tasks classes to be executed using the backend
        :backend_section: perceval backend section name
        :config: config object for the manager
        """
        super().__init__(name=backend_section)  # init the Thread
        self.config = config
        self.tasks_cls = tasks_cls  # tasks classes to be executed
        self.tasks = []  # tasks to be executed
        self.backend_section = backend_section
        self.stopper = stopper  # To stop the thread from parent
        self.timer = timer
        self.thread_id = None

    def add_task(self, task):
        self.tasks.append(task)

    def run(self):
        def __set_thread_id():
            self.thread_id = threading.get_ident()

        __set_thread_id()

        logger.debug('[%s] Task starts', self.backend_section)

        # Configure the tasks
        logger.debug(self.tasks_cls)
        for tc in self.tasks_cls:
            # create the real Task from the class
            task = tc(self.config)
            task.set_backend_section(self.backend_section)
            self.tasks.append(task)

        if not self.tasks:
            logger.debug('[%s] no tasks', self.backend_section)

        logger.debug('[%s] Tasks will be executed in this order: %s', self.backend_section, self.tasks)
        while not self.stopper.is_set():
            # we give 1 extra second to the stopper, so this loop does
            # not finish before it is set.
            time.sleep(1)

            for task in self.tasks:
                logger.debug('[%s] Tasks started: %s', self.backend_section, task)
                try:
                    task.execute()
                except Exception as ex:
                    logger.error("[%s] Exception in Task Manager %s", self.backend_section, ex, exc_info=True)
                    TasksManager.COMM_QUEUE.put(sys.exc_info())
                    raise
                logger.debug('[%s] Tasks finished: %s', self.backend_section, task)

            if self.timer > 0 and self.config.get_conf()['general']['update']:
                logger.info("[%s] sleeping for %s seconds ", self.backend_section, self.timer)
                time.sleep(self.timer)

        logger.debug('[%s] Task is exiting', self.backend_section)
