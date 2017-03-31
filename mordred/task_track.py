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
#     Alvaro del Castillo <acs@bitergia.com>
#

import logging

from grimoire_elk.elk.elastic import ElasticSearch
from grimoire_elk.track_items import fetch_track_items, get_gerrit_numbers, enrich_gerrit_items
from grimoire_elk.track_items import get_commits_from_gerrit, enrich_git_items

from mordred.task import Task

logger = logging.getLogger(__name__)

class TaskTrackItems(Task):
    """ Task to track specific items from data sources """

    ITEMS_DATA_SOURCE = 'Gerrit'

    def __init__(self, conf):
        super().__init__(conf)

    def is_backend_task(self):
        return False

    def execute(self):
        cfg = self.conf

        if 'gerrit' not in cfg or 'git' not in cfg:
            logger.error("gerrit and git are needed for track items.")
            return

        items_url = cfg['track_items']['upstream_items_url']
        project = cfg['track_items']['project']
        elastic_url_raw = cfg['track_items']['upstream_raw_es_url']
        elastic_url_enrich = cfg['es_enrichment']['url']

        index_gerrit_raw = cfg['gerrit']['raw_index']
        index_gerrit_enrich = cfg['gerrit']['enriched_index']
        index_git_raw = cfg['git']['raw_index']
        index_git_enrich = cfg['git']['enriched_index']

        db_config = {
            "database": cfg['sortinghat']['database'],
            "user": cfg['sortinghat']['user'],
            "password": cfg['sortinghat']['password'],
            "host": cfg['sortinghat']['host']
        }

        logger.info("Importing track items from %s ", items_url)

        #
        # Gerrit Reviews
        #
        gerrit_uris = fetch_track_items(items_url, self.ITEMS_DATA_SOURCE)
        gerrit_numbers = get_gerrit_numbers(gerrit_uris)
        logger.info("Total gerrit track items to be imported: %i", len(gerrit_numbers))
        enriched_items = enrich_gerrit_items(elastic_url_raw,
                                             index_gerrit_raw, gerrit_numbers,
                                             project, db_config)
        logger.info("Total gerrit track items enriched: %i", len(enriched_items))
        elastic = ElasticSearch(elastic_url_enrich, index_gerrit_enrich)
        total = elastic.bulk_upload(enriched_items, "uuid")

        #
        # Git Commits
        #
        commits_sha = get_commits_from_gerrit(elastic_url_raw,
                                              index_gerrit_raw, gerrit_numbers)
        logger.info("Total git track items to be checked: %i", len(commits_sha))
        enriched_items = enrich_git_items(elastic_url_raw,
                                          index_git_raw, commits_sha,
                                          project, db_config)
        logger.info("Total git track items enriched: %i", len(enriched_items))
        elastic = ElasticSearch(elastic_url_enrich, index_git_enrich)
        total = elastic.bulk_upload(enriched_items, "uuid")
