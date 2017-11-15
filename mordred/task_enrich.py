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

from grimoire_elk.arthur import (do_studies, enrich_backend, refresh_projects,
                                 refresh_identities)
from grimoire_elk.elastic_items import ElasticItems
from grimoire_elk.elk.elastic import ElasticSearch

from mordred.error import DataEnrichmentError
from mordred.task import Task
from mordred.task_manager import TasksManager
from mordred.task_panels import TaskPanelsAliases
from mordred.task_projects import TaskProjects


logger = logging.getLogger(__name__)


class TaskEnrich(Task):
    """ Basic class shared by all enriching tasks """

    def __init__(self, config, backend_section=None):
        super().__init__(config)
        self.backend_section = backend_section
        # This will be options in next iteration
        self.clean = False
          # check whether the aliases has beed already created
        self.enrich_aliases = False

    def __enrich_items(self):

        time_start = time.time()

        #logger.info('%s starts for %s ', 'enrichment', self.backend_section)
        logger.info('[%s] enrichment starts', self.backend_section)

        cfg = self.config.get_conf()

        if 'scroll_size' in cfg['general']:
            ElasticItems.scroll_size = cfg['general']['scroll_size']

        if 'bulk_size' in cfg['general']:
            ElasticSearch.max_items_bulk = cfg['general']['bulk_size']

        no_incremental = False
        github_token = None
        if 'github' in cfg and 'backend_token' in cfg['github']:
            github_token = cfg['github']['backend_token']
        only_studies = False
        only_identities = False

        # repos could change between executions because changes in projects
        repos = TaskProjects.get_repos_by_backend_section(self.backend_section)

        if not repos:
            logger.warning("No enrich repositories for %s", self.backend_section)

        for repo in repos:
            # First process p2o params from repo
            p2o_args = self._compose_p2o_params(self.backend_section, repo)
            filter_raw = p2o_args['filter-raw'] if 'filter-raw' in p2o_args else None
            filters_raw_prefix = p2o_args['filters-raw-prefix'] if 'filters-raw-prefix' in p2o_args else None
            jenkins_rename_file = p2o_args['jenkins-rename-file'] if 'jenkins-rename-file' in p2o_args else None
            url = p2o_args['url']
            # Second process perceval params from repo
            backend_args = self._compose_perceval_params(self.backend_section, url)

            try:
                es_col_url = self._get_collection_url()
                logger.debug('[%s] enrichment starts for %s', self.backend_section, repo)
                backend = self.get_backend(self.backend_section)
                enrich_backend(es_col_url, self.clean, backend, backend_args,
                               cfg[self.backend_section]['raw_index'],
                               cfg[self.backend_section]['enriched_index'],
                               None, #projects_db is deprecated
                               cfg['projects']['projects_file'],
                               cfg['sortinghat']['database'],
                               no_incremental, only_identities,
                               github_token,
                               False, # studies are executed in its own Task
                               only_studies,
                               cfg['es_enrichment']['url'],
                               None, #args.events_enrich
                               cfg['sortinghat']['user'],
                               cfg['sortinghat']['password'],
                               cfg['sortinghat']['host'],
                               None, #args.refresh_projects,
                               None, #args.refresh_identities,
                               author_id=None,
                               author_uuid=None,
                               filter_raw=filter_raw,
                               filters_raw_prefix=filters_raw_prefix,
                               jenkins_rename_file=jenkins_rename_file,
                               unaffiliated_group=cfg['sortinghat']['unaffiliated_group'])
            except Exception as ex:
                logger.error("Something went wrong producing enriched data for %s . " \
                             "Using the backend_args: %s ", self.backend_section, str(backend_args))
                logger.error("Exception: %s", ex)
                raise DataEnrichmentError('Failed to produce enriched data for %s', self.backend_name)

            # Let's try to create the aliases for the enriched index
            if not self.enrich_aliases:
                logger.debug("Creating aliases after enrich")
                task_aliases = TaskPanelsAliases(self.config)
                task_aliases.set_backend_section(self.backend_section)
                task_aliases.execute()
                logger.debug("Done creating aliases after enrich")
                self.enrich_aliases = True

        spent_time = time.strftime("%H:%M:%S", time.gmtime(time.time()-time_start))
        logger.info('[%s] enrichment finished in %s', self.backend_section, spent_time)

    def __autorefresh(self):
        logger.info("[%s] Refreshing project and identities " + \
                     "fields for updated uuids ", self.backend_section)
        # Refresh projects
        if False:
            # TODO: Waiting that the project info is loaded from yaml files
            logger.info("Refreshing project field in enriched index")
            enrich_backend = self._get_enrich_backend()
            field_id = enrich_backend.get_field_unique_id()
            eitems = refresh_projects(enrich_backend)
            enrich_backend.elastic.bulk_upload_sync(eitems, field_id)

        # Refresh identities
        logger.info("Refreshing identities fields in enriched index")
        enrich_backend = self._get_enrich_backend()
        field_id = enrich_backend.get_field_unique_id()
        # Now we need to get the uuids to be refreshed
        logger.debug("Checking if there are uuids to refresh in %s", self.backend_section)
        backends_uuids = TasksManager.UPDATED_UUIDS_QUEUE.get()
        if backends_uuids:
            logger.debug("Doing autorefresh for %s (%s uuids)", self.backend_section, backends_uuids)
            if backends_uuids[self.backend_section]:
                uuids_refresh = backends_uuids[self.backend_section]
                backends_uuids[self.backend_section] = []
                logger.debug("New uuids data: %s", backends_uuids)
                TasksManager.UPDATED_UUIDS_QUEUE.put(backends_uuids)
                logger.debug("Refreshing uuids %s", uuids_refresh)
                eitems = refresh_identities(enrich_backend,
                                            {"name": "author_uuid",
                                             "value": uuids_refresh})
                enrich_backend.elastic.bulk_upload_sync(eitems, field_id)
            else:
                TasksManager.UPDATED_UUIDS_QUEUE.put(backends_uuids)
        else:
            TasksManager.UPDATED_UUIDS_QUEUE.put(backends_uuids)
            logger.warning("No dict with uuids per backend to be refreshed")

    def __studies(self):
        logger.info("Executing %s studies ...", self.backend_section)
        time.sleep(5)  # Wait so enrichment has finished in ES
        enrich_backend = self._get_enrich_backend()
        do_studies(enrich_backend)

    def execute(self):
        cfg = self.config.get_conf()

        if 'enrich' in cfg[self.backend_section] and \
            cfg[self.backend_section]['enrich'] is False:
            logger.info('%s enrich disabled', self.backend_section)
            return

        # ** START SYNC LOGIC **
        # Check that identities tasks are not active before executing
        while True:
            time.sleep(10)  # check each 10s if the enrichment could start
            with TasksManager.IDENTITIES_TASKS_ON_LOCK:
                with TasksManager.NUMBER_ENRICH_TASKS_ON_LOCK:
                    in_identities = TasksManager.IDENTITIES_TASKS_ON
                    if not in_identities:
                        # The enrichment can be started
                        TasksManager.NUMBER_ENRICH_TASKS_ON += 1
                        logger.debug("Number of enrichment tasks active: %i",
                                     TasksManager.NUMBER_ENRICH_TASKS_ON)
                        break
                    else:
                        logger.debug("%s Waiting for enrich until identities is done.",
                                     self.backend_section)
        #  ** END SYNC LOGIC **

        self.__enrich_items()
        if cfg['es_enrichment']['autorefresh']:
            # Check it we should do the autorefresh
            autorefresh_backends = TasksManager.AUTOREFRESH_QUEUE.get()
            logger.debug("Checking autorefresh for %s %s", self.backend_section, autorefresh_backends)
            if autorefresh_backends[self.backend_section]:
                logger.debug("Doing autorefresh for %s", self.backend_section)
                autorefresh_backends[self.backend_section] = False
                TasksManager.AUTOREFRESH_QUEUE.put(autorefresh_backends)
                self.__autorefresh()
            else:
                logger.debug("Not doing autorefresh for %s", self.backend_section)
                TasksManager.AUTOREFRESH_QUEUE.put(autorefresh_backends)

        if cfg['es_enrichment']['studies']:
            self.__studies()

        with TasksManager.NUMBER_ENRICH_TASKS_ON_LOCK:
            TasksManager.NUMBER_ENRICH_TASKS_ON -= 1
