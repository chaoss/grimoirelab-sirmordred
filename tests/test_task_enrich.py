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
import logging
import sys
import unittest

import requests


# Hack to make sure that tests import the right packages
# due to setuptools behaviour
sys.path.insert(0, '..')

from mordred.task_enrich import TaskEnrich
from mordred.mordred import Mordred

CONF_FILE = 'test.cfg'
PROJ_FILE = 'test-projects.json'
GIT_BACKEND_SECTION = 'git'
GIT_REPO_NAME = 'https://github.com/Bitergia/mordred.git'

logging.basicConfig(level=logging.INFO)

class TestTaskEnrich(unittest.TestCase):
    """Task tests"""

    def test_initialization(self):
        """Test whether attributes are initializated"""

        morderer = Mordred(CONF_FILE)
        repos = [GIT_REPO_NAME]
        backend_section = GIT_BACKEND_SECTION
        task = TaskEnrich(morderer.conf, repos=repos, backend_section=backend_section)

        self.assertEqual(task.conf, morderer.conf)
        self.assertEqual(task.repos, repos)
        self.assertEqual(task.backend_section, backend_section)

    def test_run(self):
        """Test whether the Task could be run"""
        morderer = Mordred(CONF_FILE)
        repos = [GIT_REPO_NAME]
        backend_section = GIT_BACKEND_SECTION
        task = TaskEnrich(morderer.conf, repos=repos, backend_section=backend_section)
        self.assertEqual(task.execute(), None)

        # Check that the enrichment went well
        es_collection = morderer.conf['es_collection']
        es_enrichment = morderer.conf['es_enrichment']
        raw_index = es_collection + "/" + morderer.conf[GIT_BACKEND_SECTION]['raw_index']
        enrich_index = es_enrichment + "/" + morderer.conf[GIT_BACKEND_SECTION]['enriched_index']
        r = requests.get(raw_index+"/_search?size=0")
        raw_items = r.json()['hits']['total']
        r = requests.get(enrich_index+"/_search?size=0")
        enriched_items = r.json()['hits']['total']
        self.assertEqual(raw_items, enriched_items)


if __name__ == "__main__":
    unittest.main(warnings='ignore')
