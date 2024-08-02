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
#     Valerio Cosentino <valcos@bitergia.com>

import sys
import threading
import unittest

# Hack to make sure that tests import the right packages
# due to setuptools behaviour
sys.path.insert(0, '..')

from sirmordred.sirmordred import SirMordred
from sirmordred.config import Config
from sirmordred.task_manager import TasksManager
from sirmordred.task_collection import TaskRawDataCollection
from sirmordred.task_enrich import TaskEnrich
from sirmordred.task_projects import TaskProjects

from sortinghat.cli.client import SortingHatClient

CONF_FILE = 'test.cfg'


class TestTasksManager(unittest.TestCase):
    """TasksManager tests"""

    def setUp(self):
        self.config = Config(CONF_FILE)
        self.conf = self.config.get_conf()
        sh = self.conf.get('sortinghat')
        self.sortinghat_client = SortingHatClient(host=sh['host'], port=sh.get('port', None),
                                                  path=sh.get('path', None), ssl=sh.get('ssl', False),
                                                  user=sh['user'], password=sh['password'],
                                                  verify_ssl=sh.get('verify_ssl', True),
                                                  tenant=sh.get('tenant', True))
        self.sortinghat_client.connect()
        mordred = SirMordred(self.config)

        task = TaskProjects(self.config, self.sortinghat_client)
        self.assertEqual(task.execute(), None)

        self.backends = mordred._get_repos_by_backend()
        self.backend_tasks = [TaskRawDataCollection, TaskEnrich]
        self.stopper = threading.Event()

    def tearDown(self):
        pass

    def test_repos_by_backend(self):
        """Test whether the repos for each backend section are properly loaded"""

        self.assertTrue(list(self.backends.keys()), 36)

        backends = list(self.backends.keys())
        backends.sort()

        backend = backends[0]
        self.assertEqual(backend, 'askbot')
        self.assertEqual(self.backends[backend], ['https://ask.puppet.com'])

        backend = backends[1]
        self.assertEqual(backend, 'bugzilla')
        self.assertEqual(self.backends[backend], ['https://bugs.eclipse.org/bugs/'])

        backend = backends[2]
        self.assertEqual(backend, 'bugzillarest')
        self.assertEqual(self.backends[backend], ['https://bugzilla.mozilla.org'])

        backend = backends[3]
        self.assertEqual(backend, 'confluence')
        self.assertEqual(self.backends[backend], ['https://wiki.open-o.org/'])

        backend = backends[4]
        self.assertEqual(backend, 'discourse')
        self.assertEqual(self.backends[backend], ['https://foro.mozilla-hispano.org/'])

        backend = backends[5]
        self.assertEqual(backend, 'dockerhub')
        self.assertEqual(self.backends[backend], ['bitergia kibiter'])

        backend = backends[6]
        self.assertEqual(backend, 'functest')
        self.assertEqual(self.backends[backend], ['http://testresults.opnfv.org/test/'])

        backend = backends[7]
        self.assertEqual(backend, 'gerrit')
        self.assertEqual(self.backends[backend], ['review.openstack.org'])

        backend = backends[8]
        self.assertEqual(backend, 'git')
        self.assertEqual(self.backends[backend],
                         ["https://github.com/VizGrimoire/GrimoireLib "
                          "--filter-raw-prefix=data.files.file:grimoirelib_alch,data.files.file:README.md",
                          "https://github.com/MetricsGrimoire/CMetrics"])

        backend = backends[9]
        self.assertEqual(backend, 'github')
        self.assertEqual(self.backends[backend], ['https://github.com/grimoirelab/perceval'])

        backend = backends[10]
        self.assertEqual(backend, 'github:pull')
        self.assertEqual(self.backends[backend], ['https://github.com/grimoirelab/perceval'])

        backend = backends[11]
        self.assertEqual(backend, 'gitlab')
        self.assertEqual(self.backends[backend], ['https://gitlab.com/inkscape/inkscape-web'])

        backend = backends[12]
        self.assertEqual(backend, 'google_hits')
        self.assertEqual(self.backends[backend], ['bitergia grimoirelab'])

        backend = backends[13]
        self.assertEqual(backend, 'hyperkitty')
        self.assertEqual(self.backends[backend],
                         ['https://lists.mailman3.org/archives/list/mailman-users@mailman3.org'])

        backend = backends[14]
        self.assertEqual(backend, 'jenkins')
        self.assertEqual(self.backends[backend], ['https://build.opnfv.org/ci'])

        backend = backends[15]
        self.assertEqual(backend, 'jira')
        self.assertEqual(self.backends[backend], ['https://jira.opnfv.org'])

        backend = backends[16]
        self.assertEqual(backend, 'mattermost')
        self.assertEqual(self.backends[backend], ['https://chat.openshift.io 8j366ft5affy3p36987pcugaoa'])

        backend = backends[17]
        self.assertEqual(backend, 'mattermost:group1')
        self.assertEqual(self.backends[backend], ['https://chat.openshift.io 8j366ft5affy3p36987cip'])

        backend = backends[18]
        self.assertEqual(backend, 'mattermost:group2')
        self.assertEqual(self.backends[backend], ['https://chat.openshift.io 8j366ft5affy3p36987ciop'])

        backend = backends[19]
        self.assertEqual(backend, 'mbox')
        self.assertEqual(self.backends[backend], ['metrics-grimoire ~/.perceval/mbox'])

        backend = backends[20]
        self.assertEqual(backend, 'mediawiki')
        self.assertEqual(self.backends[backend], ['https://wiki.mozilla.org'])

        backend = backends[21]
        self.assertEqual(backend, 'meetup')
        self.assertEqual(self.backends[backend], ['South-East-Puppet-User-Group'])

        backend = backends[22]
        self.assertEqual(backend, 'mozillaclub')
        self.assertEqual(self.backends[backend],
                         ['https://spreadsheets.google.com/feeds/cells/'
                          '1QHl2bjBhMslyFzR5XXPzMLdzzx7oeSKTbgR5PM8qp64/ohaibtm/public/values?alt=json'])

        backend = backends[23]
        self.assertEqual(backend, 'nntp')
        self.assertEqual(self.backends[backend], ['news.mozilla.org mozilla.dev.project-link'])

        backend = backends[24]
        self.assertEqual(backend, 'phabricator')
        self.assertEqual(self.backends[backend], ['https://phabricator.wikimedia.org'])

        backend = backends[25]
        self.assertEqual(backend, 'pipermail')
        self.assertEqual(self.backends[backend], ['https://mail.gnome.org/archives/libart-hackers/'])

        backend = backends[26]
        self.assertEqual(backend, 'puppetforge')
        self.assertEqual(self.backends[backend], [''])

        backend = backends[27]
        self.assertEqual(backend, 'redmine')
        self.assertEqual(self.backends[backend], ['http://tracker.ceph.com/'])

        backend = backends[28]
        self.assertEqual(backend, 'remo')
        self.assertEqual(self.backends[backend], ['https://reps.mozilla.org'])

        backend = backends[29]
        self.assertEqual(backend, 'remo:activities')
        self.assertEqual(self.backends[backend], ['https://reps.mozilla.org'])

        backend = backends[30]
        self.assertEqual(backend, 'rss')
        self.assertEqual(self.backends[backend], ['https://blog.bitergia.com/feed/'])

        backend = backends[31]
        self.assertEqual(backend, 'slack')
        self.assertEqual(self.backends[backend], ['C7LSGB0AU'])

        backend = backends[32]
        self.assertEqual(backend, 'stackexchange')
        self.assertEqual(self.backends[backend],
                         ["https://stackoverflow.com/questions/tagged/ovirt",
                          "https://stackoverflow.com/questions/tagged/rdo",
                          "https://stackoverflow.com/questions/tagged/kibana"])

        backend = backends[33]
        self.assertEqual(backend, 'supybot')
        self.assertEqual(self.backends[backend],
                         ['openshift ~/.perceval/irc/percevalbot/logs/ChannelLogger/freenode/#openshift/'])

        backend = backends[34]
        self.assertEqual(backend, 'telegram')
        self.assertEqual(self.backends[backend], ['Mozilla_analytics'])

        backend = backends[35]
        self.assertEqual(backend, 'twitter')
        self.assertEqual(self.backends[backend], ['bitergia'])

    def test_initialization(self):
        """Test whether attributes are initialized"""

        small_delay = 0
        first_backend = self.backends[list(self.backends.keys())[0]]
        manager = TasksManager(self.backend_tasks, first_backend, self.stopper, self.config,
                               self.sortinghat_client, timer=small_delay)

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
        manager = TasksManager(self.backend_tasks, first_backend, self.stopper, self.config,
                               self.sortinghat_client, timer=small_delay)

        self.assertEqual(manager.tasks, [])

        for tc in manager.tasks_cls:
            task = tc(manager.config, manager.client)
            task.set_backend_section(manager.backend_section)
            manager.tasks.append(task)

        self.assertEqual(len(manager.tasks), len(manager.tasks_cls))

    def test_run_on_error(self):
        """Test whether an exception is thrown if a task fails"""

        small_delay = 0
        manager = TasksManager(self.backend_tasks, "fake-section", self.stopper,
                               self.config, self.sortinghat_client, timer=small_delay)

        with self.assertRaises(Exception):
            manager.run()


if __name__ == "__main__":
    # logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')
    unittest.main(warnings='ignore')
