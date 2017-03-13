#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Bitergia
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
#     Luis Cañas-Díaz <lcanas@bitergia.com>

import configparser
import json
import logging
import sys

from grimoire_elk.utils import get_connectors

logger = logging.getLogger(__name__)

SLEEPFOR_ERROR = """Error: You may be Arthur, King of the Britons. But you still """ + \
"""need the 'sleep_for' variable in sortinghat section\n - Mordred said."""


class Config():
    """ Class aimed to manage mordred configuration """

    def __init__(self, conf_file):
        self.conf_file = conf_file
        self.conf = None
        self.conf = self.__read_conf_files()

    def get_conf(self):
        return self.conf

    @classmethod
    def get_backend_sections(cls):
        # a backend name could include and extra ":<param>"
        # to have several backend entries with different configs
        gelk_backends = list(get_connectors().keys())
        extra_backends = ["google_hits", "remo:activities"]

        return gelk_backends + extra_backends

    def __read_conf_files(self):
        conf = {}

        logger.debug("Reading conf files")
        config = configparser.ConfigParser()
        config.read(self.conf_file)
        logger.debug(config.sections())

        if 'min_update_delay' in config['general'].keys():
            conf['min_update_delay'] = config.getint('general','min_update_delay')
        else:
            # if no parameter is included, the update won't be performed more
            # than once every minute
            conf['min_update_delay'] = 60

        # FIXME: Read all options in a generic way
        conf['es_collection'] = config.get('es_collection', 'url')
        conf['es_enrichment'] = config.get('es_enrichment', 'url')
        conf['autorefresh_on'] = config.getboolean('es_enrichment', 'autorefresh')
        conf['studies_on'] = config.getboolean('es_enrichment', 'studies')

        projects_file = config.get('projects','projects_file')
        conf['projects_file'] = projects_file
        with open(projects_file,'r') as fd:
            projects = json.load(fd)
        conf['projects'] = projects

        conf['collection_on'] = config.getboolean('phases','collection')
        conf['identities_on'] = config.getboolean('phases','identities')
        conf['enrichment_on'] = config.getboolean('phases','enrichment')
        conf['panels_on'] = config.getboolean('phases','panels')

        conf['update'] = config.getboolean('general','update')
        try:
            conf['kibana'] = config.get('general','kibana')
        except configparser.NoOptionError:
            pass

        conf['sh_bots_names'] = config.get('sortinghat', 'bots_names').split(',')
        # Optional config params
        try:
            conf['sh_no_bots_names'] = config.get('sortinghat', 'no_bots_names').split(',')
        except configparser.NoOptionError:
            pass
        conf['sh_database'] = config.get('sortinghat', 'database')
        conf['sh_host'] = config.get('sortinghat', 'host')
        conf['sh_user'] = config.get('sortinghat', 'user')
        conf['sh_password'] = config.get('sortinghat', 'password')
        aux_matching = config.get('sortinghat', 'matching')
        conf['sh_matching'] = aux_matching.replace(' ', '').split(',')
        aux_autoprofile = config.get('sortinghat', 'autoprofile')
        conf['sh_autoprofile'] = aux_autoprofile.replace(' ', '').split(',')
        conf['sh_orgs_file'] = config.get('sortinghat', 'orgs_file')
        conf['sh_load_orgs'] = config.getboolean('sortinghat', 'load_orgs')

        try:
            conf['sh_sleep_for'] = config.getint('sortinghat','sleep_for')
        except configparser.NoOptionError:
            if conf['identities_on'] and conf['update']:
                logger.error(SLEEPFOR_ERROR)
            sys.exit(1)

        try:
            conf['sh_ids_file'] = config.get('sortinghat', 'identities_file')
        except configparser.NoOptionError:
            logger.info("No identities files")


        for backend in Config.get_backend_sections():
            try:
                raw = config.get(backend, 'raw_index')
                enriched = config.get(backend, 'enriched_index')
                conf[backend] = {'raw_index':raw, 'enriched_index':enriched}
                for p in config[backend]:
                    try:
                        conf[backend][p] = config.getboolean(backend, p)
                    except ValueError:
                        conf[backend][p] = config.get(backend, p)
            except configparser.NoSectionError:
                pass

        return conf
