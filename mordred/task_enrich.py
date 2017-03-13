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
from mordred.task import Task
from mordred.error import DataEnrichmentError


logger = logging.getLogger(__name__)


class TaskEnrich(Task):
    """ Basic class shared by all enriching tasks """

    def __init__(self, conf, repos=None, backend_section=None):
        super().__init__(conf)
        self.repos = repos
        self.backend_section = backend_section
        # This will be options in next iteration
        self.clean = False

    def __enrich_items(self):
        if not self.repos:
            logger.warning("No enrich repositories for %s", self.backend_section)
            return

        time_start = time.time()

        #logger.info('%s starts for %s ', 'enrichment', self.backend_section)
        logger.info('[%s] enrichment starts', self.backend_section)

        cfg = self.conf

        no_incremental = False
        github_token = None
        if 'github' in self.conf and 'backend_token' in self.conf['github']:
            github_token = self.conf['github']['backend_token']
        only_studies = False
        only_identities = False
        for repo in self.repos:
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
                                jenkins_rename_file=jenkins_rename_file)
            except:
                logger.error("Something went wrong producing enriched data for %s . " \
                             "Using the backend_args: %s " % (self.backend_name, str(backend_args)))
                raise DataEnrichmentError('Failed to produce enriched data for %s' % self.backend_name)

        time.sleep(5)  # Safety sleep tp avoid too quick execution

        spent_time = time.strftime("%H:%M:%S", time.gmtime(time.time()-time_start))
        logger.info('[%s] enrichment finished in %s', self.backend_section, spent_time)

    def __autorefresh(self):
        logger.info("[%s] Refreshing project and identities " + \
                     "fields for all items", self.backend_section)
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
        eitems = refresh_identities(enrich_backend)
        enrich_backend.elastic.bulk_upload_sync(eitems, field_id)

    def __studies(self):
        logger.info("Executing %s studies ...", self.backend_section)
        enrich_backend = self._get_enrich_backend()
        do_studies(enrich_backend)

    def execute(self):
        if 'enrich' in self.conf[self.backend_section] and \
            self.conf[self.backend_section]['enrich'] == False:
            logger.info('%s enrich disabled', self.backend_section)
            return

        self.__enrich_items()
        if self.conf['es_enrichment']['autorefresh']:
            self.__autorefresh()
        if self.conf['es_enrichment']['studies']:
            self.__studies()
