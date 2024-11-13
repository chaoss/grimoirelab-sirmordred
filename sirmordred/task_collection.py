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
import traceback

from grimoire_elk.elk import feed_backend
from grimoire_elk.elastic_items import ElasticItems
from grimoire_elk.elastic import ElasticSearch

from grimoirelab_toolkit.datetime import datetime_utcnow

from sirmordred.error import DataCollectionError
from sirmordred.task import Task
from sirmordred.task_projects import TaskProjects


logger = logging.getLogger(__name__)


class TaskRawDataCollection(Task):
    """ Basic class shared by all collection tasks """

    def __init__(self, config, sortinghat_client=None, backend_section=None, allowed_repos=None):
        super().__init__(config, sortinghat_client)

        self.backend_section = backend_section
        self.allowed_repos = set(allowed_repos) if allowed_repos else None
        # This will be options in next iteration
        self.clean = False

    def select_aliases(self, cfg, backend_section):

        aliases_file = cfg['general']['aliases_file']
        aliases = self.load_aliases_from_json(aliases_file)
        if backend_section in aliases:
            found = aliases[backend_section]['raw']
        else:
            found = [self.get_backend(backend_section) + '-raw']

        return found

    def execute(self):

        errors = []
        cfg = self.config.get_conf()

        if 'scroll_size' in cfg['general']:
            ElasticItems.scroll_size = cfg['general']['scroll_size']

        if 'bulk_size' in cfg['general']:
            ElasticSearch.max_items_bulk = cfg['general']['bulk_size']

        if 'collect' in cfg[self.backend_section] and not cfg[self.backend_section]['collect']:
            logging.info('%s collect disabled', self.backend_section)
            return errors

        time_start = datetime_utcnow()
        logger.info('[%s] collection phase starts', self.backend_section)
        print("Collection for {}: starting...".format(self.backend_section))
        clean = False

        fetch_archive = False
        if 'fetch-archive' in cfg[self.backend_section] and cfg[self.backend_section]['fetch-archive']:
            fetch_archive = True

        anonymize = 'anonymize' in cfg[self.backend_section] and cfg[self.backend_section]['anonymize']

        # repos could change between executions because changes in projects
        repos = TaskProjects.get_repos_by_backend_section(self.backend_section)

        if not repos:
            logger.warning("No collect repositories for %s", self.backend_section)
        elif self.allowed_repos is not None:
            # Filter repos to only those specified
            repos = sorted(list(set(repos) & self.allowed_repos))

        for repo in repos:
            repo, repo_labels = self._extract_repo_tags(self.backend_section, repo)
            p2o_args = self._compose_p2o_params(self.backend_section, repo)
            filter_raw = p2o_args.get('filter-raw', None)
            no_collection = p2o_args.get('filter-no-collection', None)

            if no_collection:
                # If no-collection is set to true, the repository data is not collected.
                logging.warning("Not collecting archive repository: %s", repo)
                continue
            if filter_raw:
                # If filter-raw exists it means that there is an equivalent URL
                # in the `unknown` section of the projects.json. Thus the URL with
                # filter-raw is ignored in the collection phase, while the URL
                # in `unknown` is considered in this phase.
                logging.warning("Not collecting filter raw repository: %s", repo)
                continue

            url = p2o_args['url']
            backend_args = self._compose_perceval_params(self.backend_section, repo)
            logger.debug(backend_args)
            logger.info('[%s] collection starts for %s', self.backend_section, self.anonymize_url(repo))
            es_col_url = self._get_collection_url()
            ds = self.backend_section
            backend = self.get_backend(self.backend_section)
            project = None  # just used for github in cauldron

            es_aliases = self.select_aliases(cfg, self.backend_section)

            try:
                error_msg = feed_backend(es_col_url, clean, fetch_archive, backend, backend_args,
                                         cfg[ds]['raw_index'], cfg[ds]['enriched_index'], project,
                                         es_aliases=es_aliases, projects_json_repo=repo,
                                         repo_labels=repo_labels, anonymize=anonymize)
                error = {
                    'backend': backend,
                    'repo': repo,
                    'error': error_msg
                }

                errors.append(error)
            except Exception:
                logger.error("Something went wrong collecting data from this %s repo: %s . "
                             "Using the backend_args: %s " % (ds, url, str(backend_args)))
                traceback.print_exc()
                raise DataCollectionError('Failed to collect data from %s' % url)
            logger.info('[%s] collection finished for %s', self.backend_section, self.anonymize_url(repo))

        spent_time = str(datetime_utcnow() - time_start).split('.')[0]
        logger.info('[%s] collection phase finished in %s',
                    self.backend_section, spent_time)
        print("Collection for {}: finished after {} hours".format(self.backend_section,
                                                                  spent_time))

        self.retain_data(cfg['general']['retention_time'],
                         self.conf['es_collection']['url'],
                         self.conf[self.backend_section]['raw_index'])

        return errors
