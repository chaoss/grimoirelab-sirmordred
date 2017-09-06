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
import time
import traceback

from grimoire_elk.arthur import feed_backend
from grimoire_elk.elastic_items import ElasticItems
from grimoire_elk.elk.elastic import ElasticSearch

from mordred.error import DataCollectionError
from mordred.task import Task
from mordred.task_projects import TaskProjects


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


        if 'collect' in cfg[self.backend_section] and \
            cfg[self.backend_section]['collect'] == False:
            logging.info('%s collect disabled', self.backend_section)
            return

        t2 = time.time()
        logger.info('[%s] raw data collection starts', self.backend_section)
        clean = False

        fetch_cache = False
        if 'fetch-cache' in cfg[self.backend_section] and \
            cfg[self.backend_section]['fetch-cache']:
            fetch_cache = True

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
                feed_backend(es_col_url, clean, fetch_cache, backend, backend_args,
                             cfg[ds]['raw_index'], cfg[ds]['enriched_index'], project)
            except:
                logger.error("Something went wrong collecting data from this %s repo: %s . " \
                             "Using the backend_args: %s " % (ds, url, str(backend_args)))
                traceback.print_exc()
                raise DataCollectionError('Failed to collect data from %s' % url)


        t3 = time.time()

        spent_time = time.strftime("%H:%M:%S", time.gmtime(t3-t2))
        logger.info('[%s] Data collection finished in %s',
                    self.backend_section, spent_time)
