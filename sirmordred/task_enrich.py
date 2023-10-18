#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2021 Bitergia
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
#     Quan Zhou <quan@bitergia.com>
#

import logging
import time

from datetime import datetime, timedelta

from elasticsearch import Elasticsearch, RequestsHttpConnection

from grimoire_elk.elk import (do_studies,
                              enrich_backend,
                              refresh_projects,
                              refresh_identities,
                              retain_identities,
                              populate_identities_index)
from grimoire_elk.elastic_items import ElasticItems
from grimoire_elk.elastic import ElasticSearch
from grimoire_elk.enriched.git import GitEnrich
from grimoire_elk.utils import get_elastic
from grimoire_elk.enriched.sortinghat_gelk import SortingHat

from sirmordred.error import DataEnrichmentError
from sirmordred.task import Task
from sirmordred.task_manager import TasksManager
from sirmordred.task_projects import TaskProjects


logger = logging.getLogger(__name__)


class TaskEnrich(Task):
    """ Basic class shared by all enriching tasks """

    def __init__(self, config, backend_section=None, allowed_repos=None):
        super().__init__(config)
        self.backend_section = backend_section
        self.allowed_repos = set(allowed_repos) if allowed_repos else None
        # This will be options in next iteration
        self.clean = False
        # check whether the aliases has beed already created
        self.enrich_aliases = False
        if self.db_sh is None and self.db_host is None:
            self.db = None
        else:
            self.db = self.client

        autorefresh_interval = self.conf['es_enrichment']['autorefresh_interval']
        self.last_autorefresh = self.__update_last_autorefresh(days=autorefresh_interval)
        self.last_autorefresh_studies = self.last_autorefresh
        self.last_sortinghat_import = None

    def select_aliases(self, cfg, backend_section):

        aliases_file = cfg['general']['aliases_file']
        aliases = self.load_aliases_from_json(aliases_file)
        if backend_section in aliases:
            found = aliases[backend_section]['enrich']
        else:
            found = [self.get_backend(backend_section)]

        return found

    @staticmethod
    def __update_last_autorefresh(days=None):
        if not days:
            return datetime.utcnow()
        else:
            return datetime.utcnow() - timedelta(days=days)

    def __load_studies(self):
        studies = [study for study in self.conf[self.backend_section]['studies'] if study.strip() != ""]
        if not studies:
            logger.debug('No studies for %s' % self.backend_section)
            return None

        studies_args = []

        for study in studies:
            if study not in self.conf:
                msg = 'Missing config for study: %s' % study
                logger.error(msg)
                raise DataEnrichmentError(msg)

            study_params = self.conf[study]
            studies_args.append({"name": study,
                                 "type": study.split(":")[0],
                                 "params": study_params})

        return studies_args

    def __enrich_items(self):

        time_start = datetime.now()

        logger.info('[%s] enrichment phase starts', self.backend_section)

        cfg = self.config.get_conf()

        if 'scroll_size' in cfg['general']:
            ElasticItems.scroll_size = cfg['general']['scroll_size']

        if 'bulk_size' in cfg['general']:
            ElasticSearch.max_items_bulk = cfg['general']['bulk_size']

        no_incremental = False
        # not used due to https://github.com/chaoss/grimoirelab-elk/pull/773
        github_token = None
        pair_programming = False
        node_regex = None

        if self.backend_section in cfg and 'pair-programming' in cfg[self.backend_section]:
            pair_programming = cfg[self.backend_section]['pair-programming']
        if 'jenkins' in cfg and 'node_regex' in cfg['jenkins']:
            node_regex = cfg['jenkins']['node_regex']
        only_studies = False
        only_identities = False

        # repos could change between executions because changes in projects
        repos = TaskProjects.get_repos_by_backend_section(self.backend_section, raw=False)

        if not repos:
            logger.warning("No enrich repositories for %s", self.backend_section)
        elif self.allowed_repos is not None:
            # Filter repos to only those specified
            repos = sorted(list(set(repos) & self.allowed_repos))

        # Get the metadata__timestamp value of the last item inserted in the enriched index before
        # looping over the repos which data is stored in the same index. This is needed to make sure
        # that the incremental enrichment works for data sources that are collected globally but only
        # partially enriched.
        elastic_enrich = get_elastic(cfg['es_enrichment']['url'], cfg[self.backend_section]['enriched_index'])
        last_enrich_date = elastic_enrich.get_last_item_field("metadata__timestamp")
        if last_enrich_date:
            last_enrich_date = last_enrich_date.replace(tzinfo=None)

        for repo in repos:
            repo, repo_labels = self._extract_repo_tags(self.backend_section, repo)
            _, repo_spaces = self._extract_repo_tags(self.backend_section, repo, "spaces")
            p2o_args = self._compose_p2o_params(self.backend_section, repo)
            filter_raw = p2o_args['filter-raw'] if 'filter-raw' in p2o_args else None
            jenkins_rename_file = p2o_args['jenkins-rename-file'] if 'jenkins-rename-file' in p2o_args else None
            url = p2o_args['url']
            # Second process perceval params from repo
            backend_args = self._compose_perceval_params(self.backend_section, url)
            studies_args = None

            backend = self.get_backend(self.backend_section)
            if 'studies' in self.conf[self.backend_section] and \
                    self.conf[self.backend_section]['studies']:
                studies_args = self.__load_studies()

            logger.info('[%s] enrichment starts for %s', self.backend_section, self.anonymize_url(repo))
            es_enrich_aliases = self.select_aliases(cfg, self.backend_section)

            try:
                es_col_url = self._get_collection_url()
                enrich_backend(es_col_url, self.clean, backend, backend_args,
                               self.backend_section,
                               cfg[self.backend_section]['raw_index'],
                               cfg[self.backend_section]['enriched_index'],
                               cfg['projects']['projects_file'],
                               self.db_sh,
                               no_incremental, only_identities,
                               github_token,
                               False,  # studies are executed in its own Task
                               only_studies,
                               cfg['es_enrichment']['url'],
                               None,  # args.events_enrich
                               self.db_user,
                               self.db_password,
                               self.db_host,
                               self.db_port,
                               self.db_path,
                               self.db_ssl,
                               self.db_verify_ssl,
                               self.db_tenant,
                               None,  # args.refresh_projects,
                               None,  # args.refresh_identities,
                               author_id=None,
                               author_uuid=None,
                               filter_raw=filter_raw,
                               jenkins_rename_file=jenkins_rename_file,
                               unaffiliated_group=self.db_unaffiliate_group,
                               pair_programming=pair_programming,
                               node_regex=node_regex,
                               studies_args=studies_args,
                               es_enrich_aliases=es_enrich_aliases,
                               last_enrich_date=last_enrich_date,
                               projects_json_repo=repo,
                               repo_labels=repo_labels,
                               repo_spaces=repo_spaces)
            except Exception as ex:
                logger.error("Something went wrong producing enriched data for %s . "
                             "Using the backend_args: %s ", self.backend_section, str(backend_args))
                logger.error("Exception: %s", ex)
                raise DataEnrichmentError('Failed to produce enriched data for ' + self.backend_section)

            logger.info('[%s] enrichment finished for %s', self.backend_section, self.anonymize_url(repo))

        spent_time = str(datetime.now() - time_start).split('.')[0]
        logger.info('[%s] enrichment phase finished in %s', self.backend_section, spent_time)

    def __autorefresh(self, enrich_backend, studies=False):
        # Refresh projects
        field_id = enrich_backend.get_field_unique_id()

        if False:
            # TODO: Waiting that the project info is loaded from yaml files
            logger.info("Refreshing project field in enriched index")
            field_id = enrich_backend.get_field_unique_id()
            eitems = refresh_projects(enrich_backend)
            enrich_backend.elastic.bulk_upload(eitems, field_id)

        # Refresh identities

        if studies:
            after = self.last_autorefresh_studies
        else:
            after = self.last_autorefresh

        logger.info(f"[{self.backend_section}] Refreshing identities from {after}")

        # As we are going to recover modified identities just below, store this time
        # to make sure next iteration we are not loosing any modification, but don't
        # update corresponding field with this below until we make sure the update
        # was done in ElasticSearch
        next_autorefresh = self.__update_last_autorefresh()

        logger.debug('Getting last modified identities from SH since %s for %s', after, self.backend_section)
        author_fields = ["author_uuid"]
        try:
            meta_fields = enrich_backend.meta_fields
            author_fields += meta_fields
        except AttributeError:
            pass
        logger.debug("Refreshing identity ids for %s", self.backend_section)
        total = 0
        time_start = datetime.now()
        for individuals in SortingHat.search_last_modified_identities(self.client, after):
            eitems = refresh_identities(enrich_backend, author_fields=author_fields, individuals=individuals)
            enrich_backend.elastic.bulk_upload(eitems, field_id)
            total += len(individuals)
            logger.debug(f"[{self.backend_section}] Individuals refreshed: {total}")
        else:
            logger.debug("No ids to be refreshed found")

        spent_time = str(datetime.now() - time_start).split('.')[0]
        logger.info(f'[{self.backend_section}] Refreshed {total} identities in {spent_time}')

        # Update corresponding autorefresh date
        if studies:
            self.last_autorefresh_studies = next_autorefresh
        else:
            self.last_autorefresh = next_autorefresh

    def __autorefresh_studies(self, cfg):
        """Execute autorefresh for areas of code study if configured"""

        if 'studies' not in self.conf[self.backend_section] or \
                'enrich_areas_of_code:git' not in self.conf[self.backend_section]['studies']:
            logger.debug("Not doing autorefresh for studies, Areas of Code study is not active.")
            return

        aoc_index = self.conf['enrich_areas_of_code:git'].get('out_index', GitEnrich.GIT_AOC_ENRICHED)

        # if `out_index` exists but has no value, use default
        if not aoc_index:
            aoc_index = GitEnrich.GIT_AOC_ENRICHED

        logger.debug("Autorefresh for Areas of Code study index: %s", aoc_index)

        es = Elasticsearch([self.conf['es_enrichment']['url']], timeout=100, retry_on_timeout=True,
                           verify_certs=self._get_enrich_backend().elastic.requests.verify,
                           connection_class=RequestsHttpConnection)

        if not es.indices.exists(index=aoc_index):
            logger.debug("Not doing autorefresh, index doesn't exist for Areas of Code study")
            return

        logger.debug("Doing autorefresh for Areas of Code study")

        # Create a GitEnrich backend tweaked to work with AOC index
        aoc_backend = GitEnrich(db_sortinghat=self.db_sh, json_projects_map=cfg['projects']['projects_file'],
                                db_user=self.db_user, db_password=self.db_password, db_host=self.db_host,
                                db_port=self.db_port, db_path=self.db_path, db_ssl=self.db_ssl,
                                db_verify_ssl=self.db_verify_ssl, db_tenant=self.db_tenant)
        aoc_backend.mapping = None
        aoc_backend.roles = ['author']
        elastic_enrich = get_elastic(self.conf['es_enrichment']['url'],
                                     aoc_index, clean=False, backend=aoc_backend)
        aoc_backend.set_elastic(elastic_enrich)

        self.__autorefresh(aoc_backend, studies=True)

    def __studies(self, retention_time):
        """ Execute the studies configured for the current backend """
        log_prefix = "[" + self.backend_section + "]"
        cfg = self.config.get_conf()
        if 'studies' not in cfg[self.backend_section] or not \
           cfg[self.backend_section]['studies']:
            logger.info('%s no studies phase', log_prefix)
            return

        studies = [study for study in cfg[self.backend_section]['studies'] if study.strip() != ""]
        if not studies:
            logger.info('%s no studies phase active', log_prefix)
            return

        logger.info('%s studies phase start', log_prefix)
        time.sleep(2)  # Wait so enrichment has finished in ES
        enrich_backend = self._get_enrich_backend()
        ocean_backend = self._get_ocean_backend(enrich_backend)

        active_studies = []
        all_studies = enrich_backend.studies
        all_studies_names = [study.__name__ for study in enrich_backend.studies]

        # Time to check that configured studies are valid
        logger.debug("%s All studies: %s", log_prefix, all_studies_names)
        logger.debug("%s Configured studies %s", log_prefix, studies)
        cfg_studies_types = [study.split(":")[0] for study in studies]
        if not set(cfg_studies_types).issubset(set(all_studies_names)):
            logger.error('%s Wrong studies names: %s', log_prefix, studies)
            raise RuntimeError('Wrong studies names ', self.backend_section, studies)

        for study in enrich_backend.studies:
            if study.__name__ in cfg_studies_types:
                active_studies.append(study)

        enrich_backend.studies = active_studies
        logger.info("%s Executing studies %s" % (log_prefix, [study for study in studies]))

        studies_args = self.__load_studies()
        study_aliases = self.select_aliases(cfg, "studies_aliases")
        for study_arg in studies_args:
            alias = [study_alias['alias'] for study_alias in study_aliases if study_arg['type'] == study_alias['name']]
            if alias:
                study_arg['params']['alias'] = alias[0]

        do_studies(ocean_backend, enrich_backend, studies_args, retention_time=retention_time)
        # Return studies to its original value
        enrich_backend.studies = all_studies

        logger.info('%s studies phase end', log_prefix)

    def retain_identities(self, retention_time):
        """Retain the identities in SortingHat based on the `retention_time`
        value declared in the setup.cfg.

        :param retention_time: maximum number of minutes wrt the current date to retain the SortingHat data
        """
        enrich_es = self.conf['es_enrichment']['url']
        sortinghat_db = self.db
        sortinghat_client = self.client
        current_data_source = self.get_backend(self.backend_section)
        active_data_sources = self.config.get_active_data_sources()

        if retention_time is None:
            logger.debug("[identities retention] Retention policy disabled, no identities will be deleted.")
            return

        if retention_time <= 0:
            logger.debug("[identities retention] Retention time must be greater than 0.")
            return

        logger.info('[%s] identities retention start', self.backend_section)

        logger.info('[%s] populate identities index start', self.backend_section)
        # Upload the unique identities seen in the items to the index `grimoirelab_identities_cache`
        populate_identities_index(self.conf['es_enrichment']['url'],
                                  self.conf[self.backend_section]['enriched_index'])
        logger.info('[%s] populate identities index end', self.backend_section)

        # Delete the unique identities in SortingHat which have not been seen in
        # `grimoirelab_identities_cache` during the retention time, and delete the orphan
        # unique identities (those ones in SortingHat but not in `grimoirelab_identities_cache`)
        retain_identities(retention_time, enrich_es, sortinghat_db, current_data_source, active_data_sources)

    def execute(self):
        cfg = self.config.get_conf()

        if 'enrich' in cfg[self.backend_section] and not cfg[self.backend_section]['enrich']:
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

        try:
            self.__enrich_items()

            logger.info('[%s] data retention start', self.backend_section)
            retention_time = cfg['general']['retention_time']
            # Delete the items updated before a given date
            self.retain_data(retention_time,
                             self.conf['es_enrichment']['url'],
                             self.conf[self.backend_section]['enriched_index'])
            logger.info('[%s] data retention end', self.backend_section)

            if self.db:
                self.retain_identities(retention_time)
                logger.info('[%s] identities retention end', self.backend_section)

            autorefresh = cfg['es_enrichment']['autorefresh']

            if autorefresh and self.db:
                logger.info('[%s] autorefresh start', self.backend_section)
                self.__autorefresh(self._get_enrich_backend())
                logger.info('[%s] autorefresh end', self.backend_section)
            else:
                logger.info('[%s] autorefresh not active', self.backend_section)

            self.__studies(retention_time)

            if autorefresh and self.db:
                logger.info('[%s] autorefresh for studies start', self.backend_section)
                self.__autorefresh_studies(cfg)
                logger.info('[%s] autorefresh for studies end', self.backend_section)
            else:
                logger.info('[%s] autorefresh for studies not active', self.backend_section)

        except Exception as e:
            raise e
        finally:
            with TasksManager.NUMBER_ENRICH_TASKS_ON_LOCK:
                TasksManager.NUMBER_ENRICH_TASKS_ON -= 1
