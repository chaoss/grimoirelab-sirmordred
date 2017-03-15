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
#       Alvaro del Castillo <acs@bitergia.com>
#       Luis Cañas-Díaz <lcanas@bitergia.com>

import configparser
import json
import logging

from grimoire_elk.utils import get_connectors

logger = logging.getLogger(__name__)


class Config():
    """ Class aimed to manage mordred configuration """

    def __init__(self, conf_file):
        self.conf_file = conf_file
        self.raw_conf = None
        self.conf = self.__read_conf_files()

    @classmethod
    def backend_section_params(self):
        # Params that must exists in all backends
        params = {
            "enriched_index": {
                "optional": False,
                "default": None
            },
            "raw_index": {
                "optional": False,
                "default": None
            },
            "fetch-cache": {
                "optional": True,
                "default": True
            }
        }

        return params

    @classmethod
    def general_params(cls):
        """ Define all the possible config params """

        optional_none = {
            "optional": True,
            "default": None
        }
        no_optional_true = {
            "optional": False,
            "default": True
        }

        params = {
            "es_collection": {
                "password": optional_none,
                "user": optional_none,
                "url": {
                    "optional": False,
                    "default": "http://172.17.0.1:9200"
                }
            },
            "es_enrichment": {
                "url": {
                    "optional": False,
                    "default": "http://172.17.0.1:9200"
                },
                "studies": optional_none,
                "autorefresh": optional_none,
                "user": optional_none,
                "password": optional_none
            },
            "general": {
                "sleep": optional_none,  # we are not using it
                "min_update_delay": {
                    "optional": True,
                    "default": 60
                },
                "kibana":  {
                    "optional": True,
                    "default": 5
                },
                "update":  {
                    "optional": False,
                    "default": False
                },
                "short_name": {
                    "optional": False,
                    "default": "Short name"
                },
                "debug": {
                    "optional": False,
                    "default": True
                },
                "from_date": optional_none,  # per data source param now
                "logs_dir": {
                    "optional": False,
                    "default": "logs"
                },
            },
            "phases": {
                "identities": no_optional_true,
                "panels": no_optional_true,
                "collection": no_optional_true,
                "enrichment": no_optional_true
            },
            "projects": {
                "projects_file": {
                    "optional": False,
                    "default": "projects.json"
                },
            },
            "sortinghat": {
                "unaffiliated_group": {
                    "optional": False,
                    "default": "Unknown"
                },
                "unify_method": {  # not used
                    "optional": True,
                    "default": "fast-matching"
                },
                "matching": {
                    "optional": False,
                    "default": "email"
                },
                "sleep_for": {
                    "optional": False,
                    "default": 3600
                },
                "database": {
                    "optional": False,
                    "default": "sortinghat_db"
                },
                "host": {
                    "optional": False,
                    "default": "mariadb"
                },
                "user": {
                    "optional": False,
                    "default": "root"
                },
                "password": {
                    "optional": False,
                    "default": ""
                },
                "autoprofile": {
                    "optional": False,
                    "default": "customer, git, github"
                },
                "load_orgs": {
                    "optional": True,
                    "default": False
                },
                "orgs_file": optional_none,
                "identities_file": optional_none,
                "bots_names": optional_none,
                "no_bots_names": optional_none  # to clean bots in SH
            }
        }

        return params


    @classmethod
    def create_config_file(cls, file_path):
        logger.info("Creating config file in %s", file_path)
        general_sections = cls.general_params()
        backend_sections = cls.get_backend_sections()

        parser = configparser.ConfigParser()

        sections = list(general_sections.keys())
        sections.sort()
        for section_name in sections:
            parser.add_section(section_name)
            section = general_sections[section_name]
            params = list(section.keys())
            params.sort()
            for param in params:
                parser.set(section_name, param, str(section[param]["default"]))

        sections = backend_sections
        sections.sort()
        backend_params = cls.backend_section_params()
        params = list(cls.backend_section_params().keys())
        params.sort()
        for section_name in sections:
            parser.add_section(section_name)
            for param in params:
                if param == "enriched_index":
                    val = section_name
                elif param == "raw_index":
                    val = section_name+"-raw"
                else:
                    val = backend_params[param]['default']
                parser.set(section_name, param, str(val))

        with open(file_path, "w") as f:
            parser.write(f)

    def get_conf(self):
        return self.conf

    @classmethod
    def get_backend_sections(cls):
        # a backend name could include and extra ":<param>"
        # to have several backend entries with different configs
        gelk_backends = list(get_connectors().keys())
        extra_backends = ["google_hits", "remo:activities"]

        return gelk_backends + extra_backends

    @classmethod
    def check_config(cls, config):
        # First let's check all common sections entries
        check_params = cls.general_params()
        backend_sections = cls.get_backend_sections()

        for section in config.keys():
            if section in backend_sections or section[1:] in backend_sections:
                # backend_section or *backend_section, to be checked later
                continue
            if section not in check_params.keys():
                raise RuntimeError("Wrong section:", section)
            # Check the params for the section
            for param in config[section].keys():
                if param not in check_params[section]:
                    raise RuntimeError("Wrong section param:", section, param)
            for param in check_params[section]:
                if param not in config[section].keys():
                    if not check_params[section][param]['optional']:
                        raise RuntimeError("Missing section param:", section, param)

        # And now the backend_section entries
        # A backend section entry could have specific perceval params which are
        # not checked
        check_params = cls.backend_section_params()
        for section in config.keys():
            if section in backend_sections or section[1:] in backend_sections:
                # backend_section or *backend_section
                for param in check_params:
                    if param not in config[section].keys():
                        if not check_params[param]['optional']:
                            raise RuntimeError("Missing section param:", section, param)


    def __add_types(self, raw_conf):
        """ Convert to int, boolean, list, None types config items """

        typed_conf = {}

        for s in raw_conf.keys():
            typed_conf[s] = {}
            for option in raw_conf[s]:
                val = raw_conf[s][option]
                if len(val) > 1  and (val[0] == '"' and val[-1] == '"'):
                    # It is a string
                    typed_conf[s][option] = val[1:-1]
                # Check list
                elif len(val) > 1 and (val[0] == '[' and val[-1] == ']'):
                    # List value
                    typed_conf[s][option] = val[1:-1].replace(' ', '').split(',')
                # Check boolean
                elif val.lower() in ['true', 'false']:
                    typed_conf[s][option] = True if val.lower() == 'true' else False
                # Check None
                elif val.lower() is 'none':
                    typed_conf[s][option] = None
                else:
                    try:
                        # Check int
                        typed_conf[s][option] = int(val)
                    except ValueError:
                        # Is a string
                        typed_conf[s][option] = val
        return typed_conf

    def __read_conf_files(self):
        logger.debug("Reading conf files")
        parser = configparser.ConfigParser()
        parser.read(self.conf_file)
        raw_conf = {s:dict(parser.items(s)) for s in parser.sections()}
        config = self.__add_types(raw_conf)

        self.check_config(config)

        if 'min_update_delay' not in config['general'].keys():
            # if no parameter is included, the update won't be performed more
            # than once every minute
            config['general']['min_update_delay'] = 60

        projects_file = config['projects']['projects_file']
        with open(projects_file, 'r') as fd:
            projects = json.load(fd)
        config['projects_data'] = projects

        return config
