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
#

import configparser
import logging
import argparse
import time
import threading
import json
import sys
import requests
import random

from grimoire.arthur import feed_backend, enrich_backend
from perceval_backends import PERCEVAL_BACKENDS


class Phases:
    def __init__(self):
        self.collection = False
        self.identities = False
        self.enrichment = False

    def set_collection(self):
        self.collection = True

    def set_identities(self):
        self.identities = True

    def set_enrichment(self):
        self.enrichment = True

    def collection_enabled(self):
        return self.collection

    def identities_enabled(self):
        return self.identities

    def enrichment_enabled(self):
        return self.enrichment

class DataProcessor(threading.Thread):
    def __init__(self, phases, backend_name, repos, stopper, logger, configuration):
        super().__init__()
        self.phases = phases
        self.backend_name =  backend_name
        self.repos = repos
        self.stopper = stopper
        self.logger = logger
        self.configuration = configuration

    def _get_github_owner_repo(self, github_url):
        owner = github_url.split('/')[-2]
        repo = github_url.split('/')[-1]
        return (owner,repo)

    def _compose_perceval_params(self, backend_name, repo):
        params = []
        if backend_name == 'git':
            params.append(str(repo))
        elif backend_name == 'github':
            owner, github_repo = self._get_github_owner_repo(repo)
            params.append('--owner')
            params.append(owner)
            params.append('--repository')
            params.append(github_repo)
            params.append('--sleep-for-rate')
            params.append('-t')
            params.append(self.configuration['github']['token'])
        return params

    def enrich(self, backend_name, repos, only_identities=False):
        t2 = time.time()

        if only_identities:
            phase_name = 'Identities collection'
        else:
            phase_name = 'Data enrichment'
        self.logger.info('%s starts for %s ' % (phase_name, backend_name))

        cfg = self.configuration

        clean = False
        no_incremental = False
        github_token = None
        only_studies = False
        for r in repos:
            backend_args = self._compose_perceval_params(backend_name, r)

            # enrich_backend(url, clean, args.backend, args.backend_args,
            #                args.index, args.index_enrich,
            #                args.db_projects_map, args.db_sortinghat,
            #                args.no_incremental, args.only_identities,
            #                args.github_token,
            #                args.studies, args.only_studies,
            #                args.elastic_url_enrich)
            try:
                enrich_backend(cfg['es_collection'], clean, backend_name,
                            backend_args, #FIXME #FIXME
                            cfg[backend_name]['raw_index'],
                            cfg[backend_name]['enriched_index'],
                            cfg['projects_db'], cfg['sh_db'],
                            no_incremental, only_identities,
                            github_token,
                            cfg['studies_enabled'],
                            only_studies,
                            cfg['es_enrichment'])
            except KeyError as e:
                self.logger.exception(e)

        time.sleep(random.randint(0,20)) # FIXME test purposes

        t3 = time.time()
        spent_time = time.strftime("%H:%M:%S", time.gmtime(t3-t2))
        self.logger.info('%s finished for %s in %s' % (phase_name, backend_name, spent_time))

    def collect(self):
        t2 = time.time()
        self.logger.info('Data collection starts for %s ' % self.backend_name)
        clean = False
        fetch_cache = False
        cfg = self.configuration
        for r in self.repos:
            backend_args = self._compose_perceval_params(self.backend_name, r)

            feed_backend(cfg['es_collection'], clean, fetch_cache,
                    self.backend_name,
                    backend_args,
                    cfg[self.backend_name]['raw_index'],
                    cfg[self.backend_name]['enriched_index'],
                    r)

        # feed_backend(url, clean, args.fetch_cache,
        #              args.backend, args.backend_args,
        #              args.index, args.index_enrich, args.project)

        time.sleep(random.randint(0,20)) # FIXME test purposes

        t3 = time.time()
        spent_time = time.strftime("%H:%M:%S", time.gmtime(t3-t2))
        self.logger.info('Data collection finished for %s in %s' % (self.backend_name, spent_time))

    def extract_only_identities(self):
        #FIXME to be done, it will be a called to enrich_backend with a flag
        pass

    def run(self):
        self.logger.debug('Starting thread %s' % self.backend_name)

        # Our dear thread is executed until his mom calls him to come back home
        #
        # Phases are determined by self.phases object passsed as parameter
        while not self.stopper.is_set():
            if self.phases.collection_enabled():
                self.collect()
            if self.phases.identities_enabled():
                self.identities()
            if self.phases.enrichment_enabled():
                self.enrichment()

        self.logger.debug('Exiting thread %s' % self.backend_name)


class ElasticSearchError(Exception):
    """Exception raised for errors in the list of backends
    """
    def __init__(self, expression):
        self.expression = expression

class Mordred:

    def __init__(self, configuration_file):
        self.configuration_file = configuration_file
        self.configuration = None
        self.logger = self.setup_logs()

    def setup_logs(self):
        #logging.basicConfig(filename='/tmp/mordred.log'level=logging.DEBUG)
        logger = logging.getLogger('mordred')
        logger.setLevel(logging.INFO)

        fh = logging.FileHandler('spam.log')
        fh.setLevel(logging.DEBUG)
        # create console handler with a higher log level
        ch = logging.StreamHandler()
        ch.setLevel(logging.ERROR)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        fh.setFormatter(formatter)
        # add the handlers to logger
        logger.addHandler(ch)
        logger.addHandler(fh)
        #self.projects = None
        return logger

    def update_configuration(self, conf_obj):
        self.configuration = conf_obj

    def read_conf_files(self):
        conf = {}

        self.logger.debug("Reading configuration files")
        config = configparser.ConfigParser()
        config.read(self.configuration_file)
        self.logger.debug(config.sections())

        try:
            if 'sleep' in config['general'].keys():
                sleep = config.get('general','sleep')
            else:
                sleep = 0
            conf['sleep'] = sleep

        except KeyError:
            self.logger.error("'general' section is missing from %s " + \
                        "conf file", self.configuration_file)

        conf['es_collection'] = config.get('es_collection', 'url')
        conf['es_enrichment'] = config.get('es_enrichment', 'url')

        conf['projects_db'] = config.get('projects','database')
        projects_file = config.get('projects','projects_file')
        with open(projects_file,'r') as fd:
            projects = json.load(fd)
        conf['projects'] = projects

        conf['sh_db'] = config.get('sortinghat','database')
        for b_p in PERCEVAL_BACKENDS:
            try:
                raw = config.get(b_p, 'raw_index')
                enriched = config.get(b_p, 'enriched_index')
                conf[b_p] = {'raw_index':raw, 'enriched_index':enriched}
                if b_p == 'github':
                    conf[b_p]['token'] = config.get(b_p, 'token')
            except configparser.NoSectionError:
                pass

        conf['collection_enabled'] = config.getboolean('phases','collection')
        conf['identities_enabled'] = config.getboolean('phases','identities')
        conf['enrichment_enabled'] = config.getboolean('phases','enrichment')
        conf['studies_enabled'] = config.getboolean('phases','studies')

        return conf

    def check_write_permission(self):
        ##
        ## So far there is no way to distinguish between read and write permission
        ##
        if self.configuration['collection_enabled'] or \
            self.configuration['enrichment_enabled'] or \
            self.configuration['studies_enabled']:
            es = self.configuration['es_collection']
            r = requests.get(es, verify=False)
            if r.status_code != 200:
                raise ElasticSearchError('Is the ElasticSearch for data collection accesible?')

        if self.configuration['enrichment_enabled'] or \
            self.configuration['studies_enabled']:
            print(self.configuration['enrichment_enabled'] == True)
            print(self.configuration['studies_enabled'])
            es = self.configuration['es_enrichment']
            r = requests.get(es, verify=False)
            if r.status_code != 200:
                raise ElasticSearchError('Is the ElasticSearch for data enrichment accesible?')

    def feed_orgs_tables(self):
        print("Not implemented")

    def _get_repos_by_backend(self):
        #
        # read self.projects and return a dict of dicts with backend append
        # repos
        output = {}
        projects = self.configuration['projects']

        for p_b in PERCEVAL_BACKENDS:
            for pro in projects:
                if p_b in projects[pro]:
                    if not p_b in output:
                        output[p_b]  = projects[pro][p_b]
                    else:
                        output[p_b] = output[p_b] + projects[pro][p_b]

        self.logger.debug('repos to be retrieved: %s ' % output)
        return output

    # def _get_github_owner_repo(self, github_url):
    #     owner = github_url.split('/')[-2]
    #     repo = github_url.split('/')[-1]
    #     return (owner,repo)

    def data_collection(self):
        #
        # deprecated
        #

        if not self.configuration['collection_enabled']:
            self.logger.info("[SKIP] Data collection disabled")
            return

        threads = []
        self.logger.info('[START] Data collection starting .. ')
        t0 = time.time()

        threads = []
        stopper = threading.Event()
        rbb = self._get_repos_by_backend()
        for backend in rbb:
            # Start new Threads and add them to the threads list to complete
            # FIXME we have to pass to the function worker the backend parameters
            t = BackendFeeder(backend, rbb[backend], stopper, self.logger, self.configuration)
            #t = threading.Thread(name=backend, target=worker, args=(backend, rbb[backend]))
            threads.append(t)
            t.start()

        self.logger.info("Waiting 50 seconds before stopping")
        time.sleep(45)
        self.logger.info("Waiting 5 seconds before stopping")
        time.sleep(5)
        stopper.set()
        self.logger.info("Waiting for all threads to complete")

        # Wait for all threads to complete
        for t in threads:
            t.join()
        t1 = time.time()
        spent_time = time.strftime("%H:%M:%S", time.gmtime(t1-t0))
        self.logger.info('[END] Data collection phase finished in %s' % spent_time)

    def collect_identities(self):
        self.data_enrichment(True)

    def compose_perceval_params(self, backend_name, repo):
        params = []
        if backend_name == 'git':
            params.append(str(repo))
        elif backend_name == 'github':
            owner, github_repo = self._get_github_owner_repo(repo)
            params.append('--owner')
            params.append(owner)
            params.append('--repository')
            params.append(github_repo)
            params.append('--sleep-for-rate')
            params.append('-t')
            params.append(self.configuration['github']['token'])
        return params

    def data_enrichment(self, only_identities=False):
        #
        # deprecated
        #

        if not self.configuration['enrichment_enabled']:
            self.logger.info("[SKIP] Data enrichment disabled")
            return

        threads = []
        self.logger.info('[START] Data enrichment starting .. ')
        t0 = time.time()

        # FIXME enrich_backend_2 was here


        threads = []
        rbb = self._get_repos_by_backend()
        for backend in rbb:
            # Start new Threads and add them to the threads list to complete
            # FIXME we have to pass to the function worker the backend parameters
            t = threading.Thread(name=backend, target=enrich_backend_2, args=(backend, rbb[backend], only_identities))
            t.start()
            threads.append(t)

        # Wait for all threads to complete
        for t in threads:
            t.join()
        t1 = time.time()
        spent_time = time.strftime("%H:%M:%S", time.gmtime(t1-t0))
        self.logger.info('[END] Data enrichment phase finished in %s' % spent_time)

    def data_enrichment_studies(self):
        self.logger.info("Not implemented")

    def update_es_aliases(self):
        self.logger.info("Not implemented")

    def identities_merge(self):
        self.logger.info("Not implemented")

    def launch_data_processor(self, phases, timer):
        #
        # FIXME long description needed
        #

        self.logger.info('Data process starting .. ') # FIXME what phase?

        threads = []
        stopper = threading.Event()
        rbb = self._get_repos_by_backend()
        for backend in rbb:
            # Start new Threads and add them to the threads list to complete
            t = DataProcessor(phases, backend, rbb[backend], stopper, self.logger, self.configuration)
            threads.append(t)
            t.start()

        self.logger.info("Waiting %s seconds before stopping" % str(timer))
        time.sleep(timer)
        stopper.set()

        self.logger.info("Waiting for all threads to complete. This could take a while ..")

        # Wait for all threads to complete
        for t in threads:
            t.join()

    def run(self):

        while True:

            #FIXME with the parallel processes this is won't be read until restart
            self.update_configuration(self.read_conf_files())

            # check section enabled
            # check we have access the needed ES
            self.check_write_permission()

            # do we need ad-hoc scripts?

            # projects database, do we need to feed it?
            self.feed_orgs_tables()

            # phase one
            # we get all the items with Perceval + identites browsing the
            # raw items
            p_one = Phases()
            p_one.set_collection()
            p_one.set_identities()
            #FIXME launch DataProcessor
            self.launch_data_processor(p_one, 0)

            # unify + affiliates (phase one and a half)
            # Merge: we unify all the identities and enrol them
            self.identities_merge()

            # phase two
            # raw items + sh database with merged identities + affiliations
            # will used to produce a enriched index
            p_two = Phases()
            p_two.set_enrichment()
            self.launch_data_processor(p_two, 0)

            # phase three
            # for a fixed period of time we:
            # a) update our raw data with Perceval
            # b) get new identities and add them to SH (no merge done)
            # c) convert raw data into enriched data
            p_three = Phases()
            p_three.set_collection()
            p_three.set_enrichment()
            a_day = 86400
            self.launch_data_processor(p_three, a_day)

            # FIXME
            # reached this point a new index should be produced
            # or the one we are using should be updated with the Changes
            # for unified identities + affiliations

            # do aliases need to be changed?
            self.update_es_aliases()

def parse_args():

    parser = argparse.ArgumentParser(
        description='Mordred, the friendly friend of p2o',
        epilog='Software metrics for your peace of mind'
        )

    parser.add_argument('-c','--config', help='Configuration file',
        required=True, dest='config_file')

    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = parse_args()
    obj = Mordred(args.config_file)
    try:
        obj.run()
    except ElasticSearchError as e:
        s = 'Error: %s\n' % str(e)
        sys.stderr.write(s)
        sys.exit(1)
