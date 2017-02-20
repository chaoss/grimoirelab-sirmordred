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

from grimoire_elk.arthur import get_ocean_backend
from grimoire_elk.utils import get_connector_from_name, get_elastic

logger = logging.getLogger(__name__)

class Task():
    """ Basic class shared by all tasks """

    ES_INDEX_FIELDS = ['enriched_index', 'raw_index', 'es_collection_url']

    def __init__(self, conf):
        self.backend_name = None
        self.conf = conf
        self.db_sh = self.conf['sh_database']
        self.db_user = self.conf['sh_user']
        self.db_password = self.conf['sh_password']
        self.db_host = self.conf['sh_host']

    def is_backend_task(self):
        """
        Returns True if the Task is executed per backend.
        i.e. SortingHat unify is not executed per backend.
        """
        return True

    def run(self):
        """ Execute the Task """
        logger.debug("A bored task. It does nothing!")

    def set_repos(self, repos):
        self.repos = repos

    @classmethod
    def get_backend(self, backend_name):
        # To support the same data source with different configs
        # remo:activitites is like remo but with an extra param
        # category = activity
        backend = backend_name.split(":")[0]
        return backend

    def set_backend_name(self, backend_name):
        self.backend_name = backend_name

    def _compose_p2o_params(self, backend_name, repo):
        # get p2o params included in the projects list
        params = {}

        backend = self.get_backend(backend_name)
        connector = get_connector_from_name(backend)
        ocean = connector[1]

        # First add the params from the URL, which is backend specific
        params = ocean.get_p2o_params_from_url(repo)

        return params

    def _compose_perceval_params(self, backend_name, repo):
        # Params that are lists separated by white space
        list_params_spaces = ['blacklist-jobs']

        backend = self.get_backend(backend_name)
        connector = get_connector_from_name(backend)
        ocean = connector[1]

        # First add the params from the URL, which is backend specific
        params = ocean.get_perceval_params_from_url(repo)

        # Now add the backend params included in the config file
        for p in self.conf[backend_name]:
            if p in self.ES_INDEX_FIELDS:
                # These params are not for the perceval backend
                continue
            params.append("--"+p)
            if self.conf[backend_name][p]:
                if type(self.conf[backend_name][p]) != bool:
                    if p in list_params_spaces:
                        # '--blacklist-jobs', 'a', 'b', 'c'
                        # 'a', 'b', 'c' must be added as items in the list
                        list_params = self.conf[backend_name][p].split()
                        params += list_params
                    else:
                        params.append(self.conf[backend_name][p])
        return params

    def _get_collection_url(self):
        es_col_url = self.conf['es_collection']
        if self.backend_name and self.backend_name in self.conf:
            if 'es_collection_url' in self.conf[self.backend_name]:
                es_col_url = self.conf[self.backend_name]['es_collection_url']
        else:
            logger.warning("No config for the backend %s", self.backend_name)
        return es_col_url

    def _get_enrich_backend(self):
        db_projects_map = None
        json_projects_map = None
        clean = False
        connector = get_connector_from_name(self.get_backend(self.backend_name))

        enrich_backend = connector[2](self.db_sh, db_projects_map, json_projects_map,
                                      self.db_user, self.db_password, self.db_host)
        elastic_enrich = get_elastic(self.conf['es_enrichment'],
                                     self.conf[self.backend_name]['enriched_index'],
                                     clean, enrich_backend)
        enrich_backend.set_elastic(elastic_enrich)

        if 'github' in self.conf.keys() and \
            'backend_token' in self.conf['github'].keys() and \
            self.backend_name == "git":

            gh_token = self.conf['github']['backend_token']
            enrich_backend.set_github_token(gh_token)

        return enrich_backend

    def _get_ocean_backend(self, enrich_backend):
        backend_cmd = None

        no_incremental = False
        clean = False

        ocean_backend = get_ocean_backend(backend_cmd, enrich_backend, no_incremental)
        elastic_ocean = get_elastic(self._get_collection_url(),
                                    self.conf[self.backend_name]['raw_index'],
                                    clean, ocean_backend)
        ocean_backend.set_elastic(elastic_ocean)

        return ocean_backend
