#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2017 Bitergia
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
#     Alvaro del Castillo <acs@bitergia.com>

import json
import sys
import unittest

import httpretty

from os import remove

# Hack to make sure that tests import the right packages
# due to setuptools behaviour
sys.path.insert(0, '..')

from mordred.config import Config
from mordred.task_projects import TaskProjects


CONF_FILE = 'test.cfg'
ECLIPSE_PROJECTS_URL = 'http://projects.eclipse.org/json/projects/all'
ECLIPSE_PROJECTS_FILE = 'data/eclipse-projects.json'


def read_file(filename, mode='r'):
    with open(filename, mode) as f:
        content = f.read()
    return content


def setup_http_server():
    eclipse_projects = read_file(ECLIPSE_PROJECTS_FILE)

    http_requests = []

    def request_callback(method, uri, headers):
        last_request = httpretty.last_request()

        if uri.startswith(ECLIPSE_PROJECTS_URL):
            body = eclipse_projects
        http_requests.append(last_request)

        return (200, headers, body)

    httpretty.register_uri(httpretty.GET,
                           ECLIPSE_PROJECTS_URL,
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

    def test_run(self):
        """Test whether the Task could be run"""
        config = Config(CONF_FILE)
        task = TaskProjects(config)
        self.assertEqual(task.execute(), None)
        self.assertEqual(len(task.get_projects().keys()), 1)

    @httpretty.activate
    def test_run_eclipse(self):
        """Test whether the Task could be run getting projects from Eclipse"""
        setup_http_server()

        # Create a empty projects file for testing
        projects_file = 'test-projects-eclipse.json'

        config = Config(CONF_FILE)
        config.set_param('projects', 'load_eclipse', True)
        config.set_param('projects', 'projects_file', projects_file)
        task = TaskProjects(config)

        self.assertEqual(task.execute(), None)
        self.assertEqual(len(task.get_projects().keys()), 302)

        # Let's remove some projects to track changes
        with open(ECLIPSE_PROJECTS_FILE) as eproj:
            remove_project = 'birt'
            add_project = 'new_project'
            new_projects = task.convert_from_eclipse(json.load(eproj)['projects'])
            new_projects.pop(remove_project)
            new_projects.update({add_project: {}})
            task.set_projects(new_projects)
            self.assertEqual(task.get_projects_last_diff().sort(),
                             [add_project, remove_project].sort())

        remove(projects_file)

    @httpretty.activate
    def test_convert_from_eclipse(self):
        """Test the conversion from eclipse projects to grimoire projects"""
        setup_http_server()

        projects_file = 'test-projects-eclipse.json'
        config = Config(CONF_FILE)
        config.set_param('projects', 'load_eclipse', True)
        config.set_param('projects', 'projects_file', projects_file)
        task = TaskProjects(config)
        self.assertEqual(task.execute(), None)

        projects = task.get_projects()
        self.assertTrue(TaskProjects.GLOBAL_PROJECT in projects)

        remove(projects_file)


if __name__ == "__main__":
    # logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')
    unittest.main(warnings='ignore')
