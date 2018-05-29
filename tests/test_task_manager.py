#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 Bitergia
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
# Foundation, 51 Franklin Street, Fifth Floor, Boston, MA 02110-1335, USA.
#
# Authors:
#     Valerio Cosentino <valcos@bitergia.com>

import sys
import threading
import unittest

# Hack to make sure that tests import the right packages
# due to setuptools behaviour
sys.path.insert(0, '..')

from mordred.mordred import Mordred
from mordred.config import Config
from mordred.task_manager import TasksManager
from mordred.task_collection import TaskRawDataCollection
from mordred.task_enrich import TaskEnrich
from mordred.task_projects import TaskProjects

CONF_FILE = 'test.cfg'


class TestTasksManager(unittest.TestCase):
    """TasksManager tests"""

    def setUp(self):
        self.config = Config(CONF_FILE)
        mordred = Mordred(self.config)

        task = TaskProjects(self.config)
        self.assertEqual(task.execute(), None)

        self.backends = mordred._get_repos_by_backend()
        self.backend_tasks = [TaskRawDataCollection, TaskEnrich]
        self.stopper = threading.Event()

        # self.threads = []
        # for backend in self.backends:
        #     # Start new Threads and add them to the threads list to complete
        #     t = TasksManager(self.backend_tasks, backend, self.stopper, self.config, small_delay=0)
        #     self.threads.append(t)
        #     t.start()

    def tearDown(self):
        pass

    def test_initialization(self):
        """Test whether attributes are initializated"""

        small_delay = 0
        first_backend = self.backends[list(self.backends.keys())[0]]
        manager = TasksManager(self.backend_tasks, first_backend, self.stopper, self.config, timer=small_delay)

        self.assertEqual(manager.config, self.config)
        self.assertEqual(manager.stopper, self.stopper)
        self.assertEqual(manager.tasks_cls, self.backend_tasks)
        self.assertEqual(manager.backend_section, first_backend)
        self.assertEqual(manager.timer, small_delay)
        self.assertEqual(manager.tasks, [])

    def test_add_task(self):
        """Test whether tasks are properly added"""

        small_delay = 0
        first_backend = list(self.backends.keys())[0]
        manager = TasksManager(self.backend_tasks, first_backend, self.stopper, self.config, timer=small_delay)

        self.assertEqual(manager.tasks, [])

        for tc in manager.tasks_cls:
            task = tc(manager.config)
            task.set_backend_section(manager.backend_section)
            manager.tasks.append(task)

        self.assertEqual(len(manager.tasks), len(manager.tasks_cls))

    def test_run_on_error(self):
        """Test whether an exception is thrown if a task fails"""

        small_delay = 0
        manager = TasksManager(self.backend_tasks, "fake-section", self.stopper, self.config, timer=small_delay)

        with self.assertRaises(Exception):
            manager.run()


if __name__ == "__main__":
    # logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')
    unittest.main(warnings='ignore')
