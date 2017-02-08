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

from grimoire_elk.arthur import feed_backend
from mordred.task import Task
from mordred.error import DataCollectionError

logger = logging.getLogger(__name__)


class TaskRawDataCollection(Task):
    """ Basic class shared by all collection tasks """

    def __init__(self, conf, repos=None, backend_name=None):
        super().__init__(conf)
        self.repos = repos
        self.backend_name = backend_name
        # This will be optional in next iteration
        self.clean = False

    def run(self):
        cfg = self.conf

        if 'collect' in cfg[self.backend_name] and \
            cfg[self.backend_name]['collect'] == False:
            logging.info('%s collect disabled', self.backend_name)
            return

        t2 = time.time()
        logger.info('[%s] raw data collection starts', self.backend_name)
        clean = False

        fetch_cache = False
        if 'fetch-cache' in self.conf[self.backend_name] and \
            self.conf[self.backend_name]['fetch-cache']:
            fetch_cache = True

        for repo in self.repos:
            p2o_args = self.compose_p2o_params(self.backend_name, repo)
            filter_raw = p2o_args['filter-raw'] if 'filter-raw' in p2o_args else None

            if filter_raw:
                # If filter-raw exists the goal is to enrich already collected
                # data, so don't collect anything
                logging.warning("Not collecting filter raw repository: %s", repo)
                continue

            url = p2o_args['url']
            backend_args = self.compose_perceval_params(self.backend_name, repo)
            logger.debug(backend_args)
            logger.debug('[%s] collection starts for %s', self.backend_name, repo)
            es_col_url = self._get_collection_url()
            ds = self.backend_name

            try:
                feed_backend(es_col_url, clean, fetch_cache, ds, backend_args,
                         cfg[ds]['raw_index'], cfg[ds]['enriched_index'], url)
            except:
                logger.error("Something went wrong collecting data from this %s repo: %s . " \
                             "Using the backend_args: %s " % (ds, url, str(backend_args)))
                raise DataCollectionError('Failed to collect data from %s' % url)


        t3 = time.time()

        spent_time = time.strftime("%H:%M:%S", time.gmtime(t3-t2))
        logger.info('[%s] Data collection finished in %s', self.backend_name, spent_time)
