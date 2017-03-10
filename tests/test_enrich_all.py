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
import tarfile
import unittest
import shutil

import requests

from os.path import expanduser, join

# Hack to make sure that tests import the right packages
# due to setuptools behaviour
sys.path.insert(0, '..')

from mordred.task_enrich import TaskEnrich
from mordred.task_collection import TaskRawDataCollection
from mordred.mordred import Mordred

CONF_FILE = 'test.cfg'
PROJ_FILE = 'test-projects.json'
PERCEVAL_CACHE_FILE = './cache-test.tgz'
HOME_USER = expanduser("~")
PERCEVAL_CACHE = join(HOME_USER, '.perceval')

logging.basicConfig(level=logging.INFO)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

class TestTaskEnrichAll(unittest.TestCase):
    """ This class will test the results of full enrichments """

    @classmethod
    def setUpClass(cls):
        cls.__install_perceval_cache()

    @classmethod
    def tearDownClass(cls):
        cls.__restore_perceval_cache()

    @classmethod
    def __install_perceval_cache(self):
        logger.info("Installing the perceval cache")
        tfile = tarfile.open(PERCEVAL_CACHE_FILE, 'r:gz')
        # The cache is extracted in the default place perceval uses
        # We must use a different place but it is not easy to change that
        # because it is not configurable now in TaskRawDataCollection
        tfile.extractall("/tmp")
        shutil.move(join(PERCEVAL_CACHE, "cache"), join(PERCEVAL_CACHE, "cache.orig"))
        shutil.move("/tmp/perceval-cache/cache", PERCEVAL_CACHE)
        logger.info("Installed the perceval cache in %s", PERCEVAL_CACHE)

    @classmethod
    def __restore_perceval_cache(self):
        logger.info("Restoring the perceval cache")
        shutil.rmtree(join(PERCEVAL_CACHE, "cache"))
        shutil.move(join(PERCEVAL_CACHE, "cache.orig"), join(PERCEVAL_CACHE, "cache"))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.enrich_already_done = False

    def __collect_and_enrich(self):
        """Execute the enrich process for all backends active"""
        if not self.enrich_already_done:
            morderer = Mordred(CONF_FILE)
            repos_backend = morderer._get_repos_by_backend()
            for backend in repos_backend:
                # First collect the data
                logger.info("--- Collect %s ---\n", backend)
                task = TaskRawDataCollection(morderer.conf, repos=repos_backend[backend], backend_section=backend)
                self.assertEqual(task.execute(), None)
                # Second enrich the data
                logger.info("--- Enrich %s ---\n", backend)
                task = TaskEnrich(morderer.conf, repos=repos_backend[backend], backend_section=backend)
                self.assertEqual(task.execute(), None)
        self.enrich_already_done = True

    def test_enrich_raw_items(self):
        """ Check the number of raw items and enriched items """

        # First collect and enrich the items
        self.__collect_and_enrich()

        morderer = Mordred(CONF_FILE)
        repos_backend = morderer._get_repos_by_backend()
        for backend in repos_backend:
            # Check that the enrichment went well
            es_collection = morderer.conf['es_collection']
            es_enrichment = morderer.conf['es_enrichment']
            raw_index = es_collection + "/" + morderer.conf[backend]['raw_index']
            enrich_index = es_enrichment + "/" + morderer.conf[backend]['enriched_index']
            r = requests.get(raw_index+"/_search?size=0")
            raw_items = r.json()['hits']['total']
            r = requests.get(enrich_index+"/_search?size=0")
            enriched_items = r.json()['hits']['total']
            self.assertEqual(raw_items, enriched_items)


if __name__ == "__main__":
    unittest.main(warnings='ignore')
    print("ENDDD")