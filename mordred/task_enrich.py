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



logger = logging.getLogger(__name__)


class TaskEnrich(Task):
    """ Basic class shared by all enriching tasks """

    def __init__(self, conf, repos=None, backend_name=None):
        super().__init__(conf)
        self.repos = repos
        self.backend_name = backend_name
        # This will be options in next iteration
        self.clean = False

    def __enrich_items(self):
        time_start = time.time()

        #logger.info('%s starts for %s ', 'enrichment', self.backend_name)
        logger.info('[%s] enrichment starts', self.backend_name)

        cfg = self.conf

        no_incremental = False
        github_token = None
        if 'github' in self.conf and 'backend_token' in self.conf['github']:
            github_token = self.conf['github']['backend_token']
        only_studies = False
        only_identities=False
        for repo in self.repos:
            # First process p2o params from repo
            p2o_args = self._compose_p2o_params(self.backend_name, repo)
            filter_raw = p2o_args['filter-raw'] if 'filter-raw' in p2o_args else None
            url = p2o_args['url']
            # Second process perceval params from repo
            backend_args = self._compose_perceval_params(self.backend_name, url)

            try:
                es_col_url = self._get_collection_url()
                logger.debug('[%s] enrichment starts for %s', self.backend_name, repo)
                enrich_backend(es_col_url, self.clean, self.backend_name,
                                backend_args,
                                cfg[self.backend_name]['raw_index'],
                                cfg[self.backend_name]['enriched_index'],
                                None, #projects_db is deprecated
                                cfg['projects_file'],
                                cfg['sh_database'],
                                no_incremental, only_identities,
                                github_token,
                                False, # studies are executed in its own Task
                                only_studies,
                                cfg['es_enrichment'],
                                None, #args.events_enrich
                                cfg['sh_user'],
                                cfg['sh_password'],
                                cfg['sh_host'],
                                None, #args.refresh_projects,
                                None, #args.refresh_identities,
                                author_id=None,
                                author_uuid=None,
                                filter_raw=filter_raw)
            except KeyError as e:
                logger.exception(e)

        time.sleep(5)  # Safety sleep tp avoid too quick execution

        spent_time = time.strftime("%H:%M:%S", time.gmtime(time.time()-time_start))
        logger.info('[%s] enrichment finished in %s', self.backend_name, spent_time)

    def __autorefresh(self):
        logging.info("[%s] Refreshing project and identities " + \
                     "fields for all items", self.backend_name)
        # Refresh projects
        if False:
            # TODO: Waiting that the project info is loaded from yaml files
            logging.info("Refreshing project field in enriched index")
            enrich_backend = self._get_enrich_backend()
            field_id = enrich_backend.get_field_unique_id()
            eitems = refresh_projects(enrich_backend)
            enrich_backend.elastic.bulk_upload_sync(eitems, field_id)

        # Refresh identities
        logging.info("Refreshing identities fields in enriched index")
        enrich_backend = self._get_enrich_backend()
        field_id = enrich_backend.get_field_unique_id()
        eitems = refresh_identities(enrich_backend)
        enrich_backend.elastic.bulk_upload_sync(eitems, field_id)

    def __studies(self):
        logging.info("Executing %s studies ...", self.backend_name)
        enrich_backend = self._get_enrich_backend()
        do_studies(enrich_backend)

    def run(self):
        if 'enrich' in self.conf[self.backend_name] and \
            self.conf[self.backend_name]['enrich'] == False:
            logging.info('%s enrich disabled', self.backend_name)
            return

        self.__enrich_items()
        if self.conf['autorefresh_on']:
            self.__autorefresh()
        if self.conf['studies_on']:
            self.__studies()
