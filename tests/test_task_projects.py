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
#     Alvaro del Castillo <acs@bitergia.com>

import sys
import unittest

import httpretty

# Hack to make sure that tests import the right packages
# due to setuptools behaviour
sys.path.insert(0, '..')

from sirmordred.config import Config
from sirmordred.task_projects import TaskProjects


CONF_FILE = 'test.cfg'
PROJECTS_URL = 'http://localhost/projects.json'
URL_PROJECTS_FILE = 'data/url-projects.json'
URL_PROJECTS_MAIN = 'grimoire'

CONF_FILE_UNKNOWN = 'test-repos.cfg'


def read_file(filename, mode='r'):
    with open(filename, mode) as f:
        content = f.read()
    return content


def setup_http_server():
    url_projects = read_file(URL_PROJECTS_FILE)

    http_requests = []

    def request_callback(method, uri, headers):
        last_request = httpretty.last_request()

        body = url_projects
        http_requests.append(last_request)

        return 200, headers, body

    httpretty.register_uri(httpretty.GET,
                           PROJECTS_URL,
                           responses=[
                               httpretty.Response(body=request_callback)
                           ])

    return http_requests


class TestTaskProjects(unittest.TestCase):
    """Task tests"""

    def test_initialization(self):
        """Test whether attributes are initializated"""

        config = Config(CONF_FILE)
        task = TaskProjects(config)

        self.assertEqual(task.config, config)

    def test_get_repos_by_backend_sections_unknown(self):
        """Test whether the repos of each section are properly loaded when the unknown section is present"""

        config = Config(CONF_FILE_UNKNOWN)
        task = TaskProjects(config)
        self.assertEqual(task.execute(), None)

        # repos not in unknown
        expected_list = ["https://github.com/chaoss/grimoirelab-perceval"]

        repos = task.get_repos_by_backend_section("git")
        self.assertListEqual(repos, expected_list)

        repos = task.get_repos_by_backend_section("git", raw=False)
        self.assertListEqual(repos, expected_list)

        # repos only in unknown
        expected_list = ["https://bugzilla.mozilla.org"]

        repos = task.get_repos_by_backend_section("bugzillarest")
        self.assertListEqual(repos, expected_list)

        repos = task.get_repos_by_backend_section("bugzillarest", raw=False)
        self.assertListEqual(repos, expected_list)

        # repos in unknown and other section
        expected_list = ["gerrit.onosproject.org"]

        repos = task.get_repos_by_backend_section("gerrit:onos")
        self.assertListEqual(repos, expected_list)

        expected_list = [
            "gerrit.onosproject.org --filter-raw=data.project:OnosSystemTest",
            "gerrit.onosproject.org --filter-raw=data.project:OnosSystemTestJenkins",
            "gerrit.onosproject.org --filter-raw=data.project:cord-openwrt",
            "gerrit.onosproject.org --filter-raw=data.project:fabric-control",
            "gerrit.onosproject.org --filter-raw=data.project:manifest"
        ]

        repos = task.get_repos_by_backend_section("gerrit:onos", raw=False)
        repos.sort()
        expected_list.sort()
        self.assertListEqual(repos, expected_list)

    def test_get_repos_by_backend_section(self):
        """Test whether the repos of each section are properly loaded"""

        config = Config(CONF_FILE)
        task = TaskProjects(config)
        self.assertEqual(task.execute(), None)

        config.conf.keys()
        backend_sections = list(set([sect for sect in config.conf.keys()
                                     for backend_section in Config.get_backend_sections()
                                     if sect and sect.startswith(backend_section)]))
        backend_sections.sort()
        backend = backend_sections[0]

        repos = task.get_repos_by_backend_section(backend)
        self.assertEqual(backend, 'askbot')
        self.assertEqual(repos, ['https://ask.puppet.com'])

        backend = backend_sections[1]
        repos = task.get_repos_by_backend_section(backend)
        self.assertEqual(backend, 'bugzilla')
        self.assertEqual(repos, ['https://bugs.eclipse.org/bugs/'])

        backend = backend_sections[2]
        repos = task.get_repos_by_backend_section(backend)
        self.assertEqual(backend, 'bugzillarest')
        self.assertEqual(repos, ['https://bugzilla.mozilla.org'])

        backend = backend_sections[3]
        repos = task.get_repos_by_backend_section(backend)
        self.assertEqual(backend, 'confluence')
        self.assertEqual(repos, ['https://wiki.open-o.org/'])

        backend = backend_sections[4]
        repos = task.get_repos_by_backend_section(backend)
        self.assertEqual(backend, 'discourse')
        self.assertEqual(repos, ['https://foro.mozilla-hispano.org/'])

        backend = backend_sections[5]
        repos = task.get_repos_by_backend_section(backend)
        self.assertEqual(backend, 'dockerhub')
        self.assertEqual(repos, ['bitergia kibiter'])

        backend = backend_sections[6]
        repos = task.get_repos_by_backend_section(backend)
        self.assertEqual(backend, 'functest')
        self.assertEqual(repos, ['http://testresults.opnfv.org/test/'])

        backend = backend_sections[7]
        repos = task.get_repos_by_backend_section(backend)
        self.assertEqual(backend, 'gerrit')
        self.assertEqual(repos, ['review.openstack.org'])

        backend = backend_sections[8]
        repos = task.get_repos_by_backend_section(backend)
        repos.sort()
        expected_list = [
            "https://github.com/VizGrimoire/GrimoireLib "
            "--filter-raw-prefix=data.files.file:grimoirelib_alch,data.files.file:README.md",
            "https://github.com/MetricsGrimoire/CMetrics"]
        expected_list.sort()
        self.assertEqual(backend, 'git')
        self.assertEqual(repos, expected_list)

        backend = backend_sections[9]
        repos = task.get_repos_by_backend_section(backend)
        self.assertEqual(backend, 'github')
        self.assertEqual(repos, ['https://github.com/grimoirelab/perceval'])

        backend = backend_sections[10]
        repos = task.get_repos_by_backend_section(backend)
        self.assertEqual(backend, 'github:pull')
        self.assertEqual(repos, ['https://github.com/grimoirelab/perceval'])

        backend = backend_sections[11]
        repos = task.get_repos_by_backend_section(backend)
        self.assertEqual(backend, 'gitlab')
        self.assertEqual(repos, ['https://gitlab.com/inkscape/inkscape-web'])

        backend = backend_sections[12]
        repos = task.get_repos_by_backend_section(backend)
        self.assertEqual(backend, 'google_hits')
        self.assertEqual(repos, ['bitergia grimoirelab'])

        backend = backend_sections[13]
        repos = task.get_repos_by_backend_section(backend)
        self.assertEqual(backend, 'hyperkitty')
        self.assertEqual(repos,
                         ['https://lists.mailman3.org/archives/list/mailman-users@mailman3.org'])

        backend = backend_sections[14]
        repos = task.get_repos_by_backend_section(backend)
        self.assertEqual(backend, 'jenkins')
        self.assertEqual(repos, ['https://build.opnfv.org/ci'])

        backend = backend_sections[15]
        repos = task.get_repos_by_backend_section(backend)
        self.assertEqual(backend, 'jira')
        self.assertEqual(repos, ['https://jira.opnfv.org'])

        backend = backend_sections[16]
        repos = task.get_repos_by_backend_section(backend)
        self.assertEqual(backend, 'mattermost')
        self.assertEqual(repos, ['https://chat.openshift.io 8j366ft5affy3p36987pcugaoa'])

        backend = backend_sections[17]
        repos = task.get_repos_by_backend_section(backend)
        self.assertEqual(backend, 'mattermost:group1')
        self.assertEqual(repos, ['https://chat.openshift.io 8j366ft5affy3p36987cip'])

        backend = backend_sections[18]
        repos = task.get_repos_by_backend_section(backend)
        self.assertEqual(backend, 'mattermost:group2')
        self.assertEqual(repos, ['https://chat.openshift.io 8j366ft5affy3p36987ciop'])

        backend = backend_sections[19]
        repos = task.get_repos_by_backend_section(backend)
        self.assertEqual(backend, 'mbox')
        self.assertEqual(repos, ['metrics-grimoire ~/.perceval/mbox'])

        backend = backend_sections[20]
        repos = task.get_repos_by_backend_section(backend)
        self.assertEqual(backend, 'mediawiki')
        self.assertEqual(repos, ['https://wiki.mozilla.org'])

        backend = backend_sections[21]
        repos = task.get_repos_by_backend_section(backend)
        self.assertEqual(backend, 'meetup')
        self.assertEqual(repos, ['South-East-Puppet-User-Group'])

        backend = backend_sections[22]
        repos = task.get_repos_by_backend_section(backend)
        self.assertEqual(backend, 'mozillaclub')
        self.assertEqual(repos,
                         ['https://spreadsheets.google.com/feeds/cells/'
                          '1QHl2bjBhMslyFzR5XXPzMLdzzx7oeSKTbgR5PM8qp64/ohaibtm/public/values?alt=json'])

        backend = backend_sections[23]
        repos = task.get_repos_by_backend_section(backend)
        self.assertEqual(backend, 'nntp')
        self.assertEqual(repos, ['news.mozilla.org mozilla.dev.project-link'])

        backend = backend_sections[24]
        repos = task.get_repos_by_backend_section(backend)
        self.assertEqual(backend, 'phabricator')
        self.assertEqual(repos, ['https://phabricator.wikimedia.org'])

        backend = backend_sections[25]
        repos = task.get_repos_by_backend_section(backend)
        self.assertEqual(backend, 'pipermail')
        self.assertEqual(repos, ['https://mail.gnome.org/archives/libart-hackers/'])

        backend = backend_sections[26]
        repos = task.get_repos_by_backend_section(backend)
        self.assertEqual(backend, 'puppetforge')
        self.assertEqual(repos, [''])

        backend = backend_sections[27]
        repos = task.get_repos_by_backend_section(backend)
        self.assertEqual(backend, 'redmine')
        self.assertEqual(repos, ['http://tracker.ceph.com/'])

        backend = backend_sections[28]
        repos = task.get_repos_by_backend_section(backend)
        self.assertEqual(backend, 'remo')
        self.assertEqual(repos, ['https://reps.mozilla.org'])

        backend = backend_sections[29]
        repos = task.get_repos_by_backend_section(backend)
        self.assertEqual(backend, 'remo:activities')
        self.assertEqual(repos, ['https://reps.mozilla.org'])

        backend = backend_sections[30]
        repos = task.get_repos_by_backend_section(backend)
        self.assertEqual(backend, 'rss')
        self.assertEqual(repos, ['https://blog.bitergia.com/feed/'])

        backend = backend_sections[31]
        repos = task.get_repos_by_backend_section(backend)
        self.assertEqual(backend, 'slack')
        self.assertEqual(repos, ['C7LSGB0AU'])

        backend = backend_sections[32]
        repos = task.get_repos_by_backend_section(backend)
        self.assertEqual(backend, 'stackexchange')

        repos.sort()
        expected_list = [
            "https://stackoverflow.com/questions/tagged/ovirt",
            "https://stackoverflow.com/questions/tagged/rdo",
            "https://stackoverflow.com/questions/tagged/kibana"
        ]
        expected_list.sort()
        self.assertEqual(repos, expected_list)

        backend = backend_sections[33]
        repos = task.get_repos_by_backend_section(backend)
        self.assertEqual(backend, 'supybot')
        self.assertEqual(repos,
                         ['openshift ~/.perceval/irc/percevalbot/logs/ChannelLogger/freenode/#openshift/'])

        backend = backend_sections[34]
        repos = task.get_repos_by_backend_section(backend)
        self.assertEqual(backend, 'telegram')
        self.assertEqual(repos, ['Mozilla_analytics'])

        backend = backend_sections[35]
        repos = task.get_repos_by_backend_section(backend)
        self.assertEqual(backend, 'twitter')
        self.assertEqual(repos, ['bitergia'])

    def test_run(self):
        """Test whether the Task could be run"""
        config = Config(CONF_FILE)
        task = TaskProjects(config)
        self.assertEqual(task.execute(), None)
        self.assertEqual(len(task.get_projects().keys()), 1)

    def test__get_projects_from_url(self):
        """Test downloading projects from an URL """
        setup_http_server()

        projects_url = 'http://localhost/projects.json'
        config = Config(CONF_FILE)
        config.set_param('projects', 'projects_url', projects_url)
        task = TaskProjects(config)

        httpretty.enable(allow_net_connect=True)
        self.assertEqual(task.execute(), None)

        projects = task.get_projects()
        self.assertTrue(URL_PROJECTS_MAIN in projects)
        httpretty.disable()


if __name__ == "__main__":
    # logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')
    unittest.main(warnings='ignore')
