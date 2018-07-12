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

import inspect
import json
import logging
import os
import pickle
import sys
import time
import traceback

from threading import Lock

import redis

import requests

from arthur.common import Q_STORAGE_ITEMS

from grimoire_elk.elk import feed_backend
from grimoire_elk.elastic_items import ElasticItems
from grimoire_elk.elastic import ElasticSearch
from grimoire_elk.utils import get_connector_from_name, get_elastic

from sirmordred.error import DataCollectionError
from sirmordred.task import Task
from sirmordred.task_projects import TaskProjects


logger = logging.getLogger(__name__)


class TaskRawDataCollection(Task):
    """ Basic class shared by all collection tasks """

    def __init__(self, config, backend_section=None):
        super().__init__(config)

        self.backend_section = backend_section
        # This will be options in next iteration
        self.clean = False

    def execute(self):
        cfg = self.config.get_conf()

        if 'scroll_size' in cfg['general']:
            ElasticItems.scroll_size = cfg['general']['scroll_size']

        if 'bulk_size' in cfg['general']:
            ElasticSearch.max_items_bulk = cfg['general']['bulk_size']

        if ('collect' in cfg[self.backend_section] and
                not cfg[self.backend_section]['collect']):
            logging.info('%s collect disabled', self.backend_section)
            return

        t2 = time.time()
        logger.info('[%s] raw data collection starts', self.backend_section)
        print("Collection for {}: starting...".format(self.backend_section))
        clean = False

        fetch_archive = False
        if ('fetch-archive' in cfg[self.backend_section] and
            cfg[self.backend_section]['fetch-archive']):
            fetch_archive = True

        # repos could change between executions because changes in projects
        repos = TaskProjects.get_repos_by_backend_section(self.backend_section)

        if not repos:
            logger.warning("No collect repositories for %s", self.backend_section)

        for repo in repos:
            p2o_args = self._compose_p2o_params(self.backend_section, repo)
            filter_raw = p2o_args['filter-raw'] if 'filter-raw' in p2o_args else None

            if filter_raw:
                # If filter-raw exists the goal is to enrich already collected
                # data, so don't collect anything
                logging.warning("Not collecting filter raw repository: %s", repo)
                continue

            url = p2o_args['url']
            backend_args = self._compose_perceval_params(self.backend_section, repo)
            logger.debug(backend_args)
            logger.debug('[%s] collection starts for %s', self.backend_section, repo)
            es_col_url = self._get_collection_url()
            ds = self.backend_section
            backend = self.get_backend(self.backend_section)
            project = None  # just used for github in cauldron
            try:
                feed_backend(es_col_url, clean, fetch_archive, backend, backend_args,
                             cfg[ds]['raw_index'], cfg[ds]['enriched_index'], project)
            except Exception:
                logger.error("Something went wrong collecting data from this %s repo: %s . "
                             "Using the backend_args: %s " % (ds, url, str(backend_args)))
                traceback.print_exc()
                raise DataCollectionError('Failed to collect data from %s' % url)

        t3 = time.time()

        spent_time = time.strftime("%H:%M:%S", time.gmtime(t3 - t2))
        logger.info('[%s] Data collection finished in %s',
                    self.backend_section, spent_time)
        print("Collection for {}: finished after {} hours".format(self.backend_section,
                                                                  spent_time))


class TaskRawDataArthurCollection(Task):
    """ Basic class to control arthur for data collection """

    ARTHUR_TASK_DELAY = 60  # sec, it should be configured per kind of backend
    REPOSITORY_DIR = "/tmp"
    ARTHUR_FEED_LOCK = Lock()
    ARTHUR_LAST_MEMORY_CHECK = time.time()
    ARTHUR_LAST_MEMORY_CHECK_TIME = 0  # seconds needed to check the memory
    ARTHUR_LAST_MEMORY_SIZE = 0  # size in MB of the python dict
    ARTHUR_MAX_MEMORY_SIZE = 200  # max size in MB of the python dict
    ARTHUR_REDIS_ITEMS = 1000  # number of raw items to collect from redis

    arthur_items = {}  # Hash with tag list with all items collected from arthur queue

    def __init__(self, config, backend_section=None):
        super().__init__(config)

        self.arthur_url = config.get_conf()['es_collection']['arthur_url']

        self.backend_section = backend_section

    # https://goshippo.com/blog/measure-real-size-any-python-object/
    @classmethod
    def measure_memory(cls, obj, seen=None):
        """Recursively finds size of objects"""
        size = sys.getsizeof(obj)
        if seen is None:
            seen = set()
        obj_id = id(obj)
        if obj_id in seen:
            return 0
        # Important mark as seen *before* entering recursion to gracefully handle
        # self-referential objects
        seen.add(obj_id)
        if isinstance(obj, dict):
            size += sum([cls.measure_memory(v, seen) for v in obj.values()])
            size += sum([cls.measure_memory(k, seen) for k in obj.keys()])
        elif hasattr(obj, '__dict__'):
            size += cls.measure_memory(obj.__dict__, seen)
        elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
            size += sum([cls.measure_memory(i, seen) for i in obj])
        return size

    def __feed_arthur(self):
        """ Feed Ocean with backend data collected from arthur redis queue"""

        with self.ARTHUR_FEED_LOCK:

            # This is a expensive operation so don't do it always
            if (time.time() - self.ARTHUR_LAST_MEMORY_CHECK) > 5 * self.ARTHUR_LAST_MEMORY_CHECK_TIME:
                self.ARTHUR_LAST_MEMORY_CHECK = time.time()
                logger.debug("Measuring the memory used by the raw items dict ...")
                try:
                    memory_size = self.measure_memory(self.arthur_items) / (1024 * 1024)
                except RuntimeError as ex:
                    # During memory usage measure, other thread could change the dict
                    logger.warning("Can't get the memory used by the raw items dict: %s", ex)
                    memory_size = self.ARTHUR_LAST_MEMORY_SIZE
                self.ARTHUR_LAST_MEMORY_CHECK_TIME = time.time() - self.ARTHUR_LAST_MEMORY_CHECK
                logger.debug("Arthur items memory size: %0.2f MB (%is to check)",
                             memory_size, self.ARTHUR_LAST_MEMORY_CHECK_TIME)
                self.ARTHUR_LAST_MEMORY_SIZE = memory_size

            # Don't feed items from redis if the current python dict is
            # larger than ARTHUR_MAX_MEMORY_SIZE

            if self.ARTHUR_LAST_MEMORY_SIZE > self.ARTHUR_MAX_MEMORY_SIZE:
                logger.debug("Items queue full. Not collecting items from redis queue.")
                return

            logger.info("Collecting items from redis queue")

            db_url = self.config.get_conf()['es_collection']['redis_url']

            conn = redis.StrictRedis.from_url(db_url)
            logger.debug("Redis connection stablished with %s.", db_url)

            # Get and remove queued items in an atomic transaction
            pipe = conn.pipeline()
            # pipe.lrange(Q_STORAGE_ITEMS, 0, -1)
            pipe.lrange(Q_STORAGE_ITEMS, 0, self.ARTHUR_REDIS_ITEMS - 1)
            pipe.ltrim(Q_STORAGE_ITEMS, self.ARTHUR_REDIS_ITEMS, -1)
            items = pipe.execute()[0]

            for item in items:
                arthur_item = pickle.loads(item)
                if arthur_item['tag'] not in self.arthur_items:
                    self.arthur_items[arthur_item['tag']] = []
                self.arthur_items[arthur_item['tag']].append(arthur_item)

            for tag in self.arthur_items:
                if self.arthur_items[tag]:
                    logger.debug("Arthur items for %s: %i", tag, len(self.arthur_items[tag]))

    def backend_tag(self, repo):
        tag = repo  # the default tag in general
        if 'tag' in self.conf[self.backend_section]:
            tag = self.conf[self.backend_section]['tag']
        if self.backend_section in ["git", "github"]:
            # The same repo could appear in git and github data sources
            # Two tasks in arthur can not have the same tag
            tag = repo + "_" + self.backend_section
        if self.backend_section in ["mediawiki"]:
            tag = repo.split()[0]

        return tag

    def __feed_backend_arthur(self, repo):
        """ Feed Ocean with backend data collected from arthur redis queue"""

        # Always get pending items from arthur for all data sources
        self.__feed_arthur()

        tag = self.backend_tag(repo)

        logger.debug("Arthur items available for %s", self.arthur_items.keys())

        logger.debug("Getting arthur items for %s.", tag)

        if tag in self.arthur_items:
            logger.debug("Found items for %s.", tag)
            while self.arthur_items[tag]:
                yield self.arthur_items[tag].pop()

    def __create_arthur_json(self, repo, backend_args):
        """ Create the JSON for configuring arthur to collect data

        https://github.com/grimoirelab/arthur#adding-tasks
        Sample for git:

        {
        "tasks": [
            {
                "task_id": "arthur.git",
                "backend": "git",
                "backend_args": {
                    "gitpath": "/tmp/arthur_git/",
                    "uri": "https://github.com/grimoirelab/arthur.git"
                },
                "category": "commit",
                "archive_args": {
                    "archive_path": '/tmp/test_archives',
                    "fetch_from_archive": false,
                    "archive_after": None
                },
                "scheduler_args": {
                    "delay": 10
                }
            }
        ]
        }
        """

        backend_args = self._compose_arthur_params(self.backend_section, repo)
        if self.backend_section == 'git':
            backend_args['gitpath'] = os.path.join(self.REPOSITORY_DIR, repo)
        backend_args['tag'] = self.backend_tag(repo)

        ajson = {"tasks": [{}]}
        # This is the perceval tag
        ajson["tasks"][0]['task_id'] = self.backend_tag(repo)
        ajson["tasks"][0]['backend'] = self.backend_section.split(":")[0]
        ajson["tasks"][0]['backend_args'] = backend_args
        ajson["tasks"][0]['category'] = backend_args['category']
        ajson["tasks"][0]['archive'] = {}
        ajson["tasks"][0]['scheduler'] = {"delay": self.ARTHUR_TASK_DELAY}
        # from-date or offset param must be added
        es_col_url = self._get_collection_url()
        es_index = self.conf[self.backend_section]['raw_index']
        # Get the last activity for the data source
        es = ElasticSearch(es_col_url, es_index)
        connector = get_connector_from_name(self.backend_section)

        klass = connector[0]  # Backend for the connector
        signature = inspect.signature(klass.fetch)

        last_activity = None
        filter_ = {"name": "tag", "value": backend_args['tag']}
        if 'from_date' in signature.parameters:
            last_activity = es.get_last_item_field('metadata__updated_on', [filter_])
            if last_activity:
                ajson["tasks"][0]['backend_args']['from_date'] = last_activity.isoformat()
        elif 'offset' in signature.parameters:
            last_activity = es.get_last_item_field('offset', [filter_])
            if last_activity:
                ajson["tasks"][0]['backend_args']['offset'] = last_activity

        if last_activity:
            logging.info("Getting raw item with arthur since %s", last_activity)

        return(ajson)

    def execute(self):

        def check_arthur_task(repo, backend_args):
            """ Check if a task exists in arthur and if not, create it """
            arthur_repo_json = self.__create_arthur_json(repo, backend_args)
            logger.debug('JSON config for arthur %s', json.dumps(arthur_repo_json, indent=True))

            # First check is the task already exists
            try:
                r = requests.post(self.arthur_url + "/tasks")
            except requests.exceptions.ConnectionError as ex:
                logging.error("Can not connect to %s", self.arthur_url)
                raise RuntimeError("Can not connect to " + self.arthur_url)

            task_ids = [task['task_id'] for task in r.json()['tasks']]
            new_task_ids = [task['task_id'] for task in arthur_repo_json['tasks']]
            # TODO: if a tasks already exists maybe we should delete and readd it
            already_tasks = list(set(task_ids).intersection(set(new_task_ids)))
            if len(already_tasks) > 0:
                logger.warning("Tasks not added to arthur because there are already existing tasks %s", already_tasks)
            else:
                r = requests.post(self.arthur_url + "/add", json=arthur_repo_json)
                r.raise_for_status()
                logger.info('[%s] collection configured in arthur for %s', self.backend_section, repo)

        def collect_arthur_items(repo):
            aitems = self.__feed_backend_arthur(repo)
            if not aitems:
                return
            connector = get_connector_from_name(self.backend_section)
            klass = connector[1]  # Ocean backend for the connector
            ocean_backend = klass(None)
            es_col_url = self._get_collection_url()
            es_index = self.conf[self.backend_section]['raw_index']
            clean = False
            elastic_ocean = get_elastic(es_col_url, es_index, clean, ocean_backend)
            ocean_backend.set_elastic(elastic_ocean)
            ocean_backend.feed(arthur_items=aitems)

        cfg = self.config.get_conf()

        if ('collect' in cfg[self.backend_section] and
            not cfg[self.backend_section]['collect']):
            logging.info('%s collect disabled', self.backend_section)
            return

        if 'scroll_size' in cfg['general']:
            ElasticItems.scroll_size = cfg['general']['scroll_size']

        if 'bulk_size' in cfg['general']:
            ElasticSearch.max_items_bulk = cfg['general']['bulk_size']

        logger.info('Programming arthur for [%s] raw data collection', self.backend_section)
        clean = False

        fetch_archive = False
        if ('fetch-archive' in self.conf[self.backend_section] and
            self.conf[self.backend_section]['fetch-archive']):
            fetch_archive = True

        # repos could change between executions because changes in projects
        repos = TaskProjects.get_repos_by_backend_section(self.backend_section)

        if not repos:
            logger.warning("No collect repositories for %s", self.backend_section)

        for repo in repos:
            # If the repo already exists don't try to add it to arthur
            tag = self.backend_tag(repo)
            if tag not in self.arthur_items:
                self.arthur_items[tag] = []
                p2o_args = self._compose_p2o_params(self.backend_section, repo)
                filter_raw = p2o_args['filter-raw'] if 'filter-raw' in p2o_args else None
                if filter_raw:
                    # If filter-raw exists the goal is to enrich already collected
                    # data, so don't collect anything
                    logging.warning("Not collecting filter raw repository: %s", repo)
                    continue
                backend_args = self._compose_perceval_params(self.backend_section, repo)
                logger.debug(backend_args)

                check_arthur_task(repo, backend_args)

            collect_arthur_items(repo)
