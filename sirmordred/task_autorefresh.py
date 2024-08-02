# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 Bitergia
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
#     Jose Javier Merchante <jjmerchante@bitergia.com>
#

import logging
import ssl

from datetime import datetime

from elasticsearch import Elasticsearch
from elasticsearch.connection import create_ssl_context

from grimoire_elk.elk import refresh_identities
from grimoire_elk.enriched.git import GitEnrich
from grimoire_elk.utils import get_elastic, get_connector_from_name
from grimoire_elk.enriched.sortinghat_gelk import SortingHat

from sirmordred.config import Config
from sirmordred.task import Task
from sirmordred.task_projects import TaskProjects


logger = logging.getLogger(__name__)


class TaskAutorefresh(Task):
    """Refresh the last modified identities for all the backends."""

    def __init__(self, config, sortinghat_client):
        super().__init__(config, sortinghat_client)

        self.last_autorefresh_backend = {}

    def is_backend_task(self):
        return False

    def _get_backend_sections(self):
        """Get all the backends' sections enabled"""

        backends = []
        projects = TaskProjects.get_projects()

        for pro in projects:
            for sect in projects[pro].keys():
                for backend_section in Config.get_backend_sections():
                    if sect.startswith(backend_section) and sect in self.conf:
                        backends.append(sect)

        # Remove duplicates
        backends = list(set(backends))
        return backends

    def __autorefresh(self, enrich_backend, backend_section, after):
        """Refresh identities for a specific backend or study after a specific date"""

        logger.info(f"[{backend_section}] Refreshing identities from {after}")

        field_id = enrich_backend.get_field_unique_id()
        author_fields = ["author_uuid"]
        try:
            meta_fields = enrich_backend.meta_fields
            author_fields += meta_fields
        except AttributeError:
            pass

        total_indiv = 0
        total_items = 0
        time_start = datetime.now()
        for individuals in SortingHat.search_last_modified_identities(self.client, after):
            eitems = refresh_identities(enrich_backend, author_fields=author_fields, individuals=individuals)
            total_items += enrich_backend.elastic.bulk_upload(eitems, field_id)
            total_indiv += len(individuals)
            logger.debug(f"[{backend_section}] Individuals/items refreshed: {total_indiv}/{total_items}")

        spent_time = str(datetime.now() - time_start).split('.')[0]
        logger.info(f'[{backend_section}] Refreshed {total_indiv} individuals and {total_items} items in {spent_time}')

    def __autorefresh_areas_of_code(self, after):
        """Execute autorefresh for areas of code study if configured"""

        if 'git' not in self.conf or \
           'studies' not in self.conf['git'] or \
           'enrich_areas_of_code:git' not in self.conf['git']['studies']:
            logger.info("Not doing autorefresh for studies, Areas of Code study is not active.")
            return

        aoc_index = self.conf['enrich_areas_of_code:git'].get('out_index', GitEnrich.GIT_AOC_ENRICHED)
        if not aoc_index:
            aoc_index = GitEnrich.GIT_AOC_ENRICHED

        logger.debug(f"Autorefresh for Areas of Code study index: {aoc_index}")

        ssl_context = create_ssl_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        es = Elasticsearch(hosts=[self.conf['es_enrichment']['url']],
                           timeout=100, retry_on_timeout=True, ssl_context=ssl_context)

        if not es.indices.exists(index=aoc_index):
            logger.debug("Not doing autorefresh, index doesn't exist for Areas of Code study")
            return

        logger.debug("Doing autorefresh for Areas of Code study")

        # Create a GitEnrich backend tweaked to work with AOC index
        json_projects_map = self.conf['projects']['projects_file']
        aoc_backend = GitEnrich(db_sortinghat=self.db_sh, json_projects_map=json_projects_map,
                                db_user=self.db_user, db_password=self.db_password, db_host=self.db_host,
                                db_port=self.db_port, db_path=self.db_path, db_ssl=self.db_ssl,
                                db_verify_ssl=self.db_verify_ssl, db_tenant=self.db_tenant)
        aoc_backend.mapping = None
        aoc_backend.roles = ['author']
        elastic_enrich = get_elastic(url=self.conf['es_enrichment']['url'], es_index=aoc_index,
                                     clean=False, backend=aoc_backend)
        aoc_backend.set_elastic(elastic_enrich)
        if self.db_unaffiliate_group:
            aoc_backend.unaffiliated_group = self.db_unaffiliate_group

        self.__autorefresh(aoc_backend, 'git:aoc', after)

    def __get_enrich_backend(self, backend):
        connector = get_connector_from_name(backend)

        json_projects_map = self.conf['projects']['projects_file']
        enrich_backend = connector[2](db_sortinghat=self.db_sh, json_projects_map=json_projects_map,
                                      db_user=self.db_user, db_password=self.db_password, db_host=self.db_host,
                                      db_port=self.db_port, db_path=self.db_path, db_ssl=self.db_ssl,
                                      db_verify_ssl=self.db_verify_ssl, db_tenant=self.db_tenant)
        elastic_enrich = get_elastic(url=self.conf['es_enrichment']['url'],
                                     es_index=self.conf[backend]['enriched_index'],
                                     clean=False, backend=enrich_backend)
        enrich_backend.set_elastic(elastic_enrich)

        if 'pair-programming' in self.conf[backend]:
            enrich_backend.pair_programming = self.conf[backend]['pair-programming']

        if self.db_unaffiliate_group:
            enrich_backend.unaffiliated_group = self.db_unaffiliate_group

        return enrich_backend

    def execute(self):
        """Run autorefresh for all the backends"""

        autorefresh = self.conf['es_enrichment']['autorefresh']
        if not autorefresh or not self.client:
            logger.info('Periodic autorefresh not active')
            return

        backends = self._get_backend_sections()
        for backend_section in backends:
            after = self.last_autorefresh_backend.get(backend_section, datetime.utcnow())
            self.last_autorefresh_backend[backend_section] = datetime.utcnow()

            logger.info(f'[{backend_section}] Periodic autorefresh start')
            enrich_backend = self.__get_enrich_backend(backend_section)
            self.__autorefresh(enrich_backend, backend_section, after)
            logger.info(f'[{backend_section}] Periodic autorefresh end')

        after = self.last_autorefresh_backend.get('git:aoc', datetime.utcnow())
        self.last_autorefresh_backend['git:aoc'] = datetime.utcnow()

        logger.info('[git:aoc] Periodic autorefresh for studies starts')
        self.__autorefresh_areas_of_code(after)
        logger.info('[git:aoc] Periodic autorefresh for studies ends')
