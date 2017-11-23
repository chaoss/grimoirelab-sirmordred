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
    """Class aimed to manage mordred configuration"""

    def __init__(self, conf_file, conf_list=[]):
        """Initialize object.

        The object can be initialized with a configuration file,
        and, optionally, with a list of other configuration files.
        If the list of other configuration files exist, it will
        be read, in order, after the configuration file.
        Values set in a file read later will overwrite values set
        in files read earlier. Values not set by any file will
        be set to the default values, when possible.

        :param conf_file; configuration file name
        :param conf_list: list of other configuration files (default: empty)
        """

        self.conf_list = [conf_file] + conf_list
        self.raw_conf = None
        # Build self.conf
        self.__read_conf_files()

        # If projects are not already loaded do it
        from .task_projects import TaskProjects
        if not TaskProjects.get_projects():
            # logging is not yet ready
            print("Loading projects")
            TaskProjects(self).execute()
            print("Done")

    @classmethod
    def backend_section_params(self):
        # Params that must exists in all backends
        params = {
            "enriched_index": {
                "optional": False,
                "default": None,
                "type": str

            },
            "raw_index": {
                "optional": False,
                "default": None,
                "type": str
            },
            "fetch-cache": {
                "optional": True,
                "default": True,
                "type": bool
            }
        }

        return params

    @classmethod
    def general_params(cls):
        """ Define all the possible config params """

        optional_bool_none = {
            "optional": True,
            "default": None,
            "type": bool
        }
        optional_string_none = {
            "optional": True,
            "default": None,
            "type": str
        }
        optional_int_none = {
            "optional": True,
            "default": None,
            "type": int
        }
        optional_empty_list = {
            "optional": True,
            "default": [],
            "type": list
        }
        no_optional_empty_string = {
            "optional": False,
            "default": "",
            "type": str
        }
        no_optional_true = {
            "optional": False,
            "default": True,
            "type": bool
        }
        optional_false = {
            "optional": True,
            "default": False,
            "type": bool
        }

        params = {}

        # GENERAL CONFIG
        params_general = {
            "general": {
                "sleep": optional_int_none,  # we are not using it
                "min_update_delay": {
                    "optional": True,
                    "default": 60,
                    "type": int
                },
                "kibana":  {
                    "optional": True,
                    "default": "5",
                    "type": str
                },
                "update":  {
                    "optional": False,
                    "default": False,
                    "type": bool
                },
                "short_name": {
                    "optional": False,
                    "default": "Short name",
                    "type": str
                },
                "debug": {
                    "optional": False,
                    "default": True,
                    "type": bool
                },
                "from_date": optional_string_none,  # per data source param now
                "logs_dir": {
                    "optional": False,
                    "default": "logs",
                    "type": str
                },
                "skip_initial_load": {
                    "optional": True,
                    "default": False,
                    "type": bool
                },
                "bulk_size": {
                    "optional": True,
                    "default": 1000,
                    "type": int
                },
                "scroll_size": {
                    "optional": True,
                    "default": 100,
                    "type": int
                }

            }
        }
        params_projects = {
            "projects": {
                "projects_file": {
                    "optional": False,
                    "default": "projects.json",
                    "type": str
                },
                "load_eclipse": {
                    "optional": True,
                    "default": False,
                    "type": bool
                }
            }
        }

        params_phases = {
            "phases": {
                "collection": no_optional_true,
                "enrichment": no_optional_true,
                "identities": no_optional_true,
                "panels": no_optional_true,
                "track_items": optional_false,
                "report": optional_false
            }
        }

        general_config_params = [params_general, params_projects, params_phases]

        for section_params in general_config_params:
            params.update(section_params)

        # Config provided by tasks
        params_collection = {
            "es_collection": {
                "password": optional_string_none,
                "user": optional_string_none,
                "url": {
                    "optional": False,
                    "default": "http://172.17.0.1:9200",
                    "type": str
                }
            }
        }

        params_enrichment = {
            "es_enrichment": {
                "url": {
                    "optional": False,
                    "default": "http://172.17.0.1:9200",
                    "type": str
                },
                "studies": optional_bool_none,
                "autorefresh": {
                    "optional": True,
                    "default": True,
                    "type": bool
                },
                "user": optional_string_none,
                "password": optional_string_none
            }
        }

        params_panels = {
            "panels": {
                "kibiter_time_from": {
                    "optional": True,
                    "default": "now-90d",
                    "type": str
                },
                "kibiter_default_index": {
                    "optional": True,
                    "default": "git",
                    "type": str
                }
            }
        }

        params_report = {
            "report": {
                "start_date": {
                    "optional": False,
                    "default": "1970-01-01",
                    "type": str
                },
                "end_date": {
                    "optional": False,
                    "default": "2100-01-01",
                    "type": str
                },
                "interval": {
                    "optional": False,
                    "default": "quarter",
                    "type": str
                },
                "config_file": {
                    "optional": False,
                    "default": "report.cfg",
                    "type": str
                },
                "data_dir": {
                    "optional": False,
                    "default": "report_data",
                    "type": str
                },
                "filters": optional_empty_list,
                "offset": optional_string_none
            }
        }

        params_sortinghat = {
            "sortinghat": {
                "affiliate": {
                    "optional": False,
                    "default": "True",
                    "type": bool
                },
                "unaffiliated_group": {
                    "optional": False,
                    "default": "Unknown",
                    "type": str
                },
                "unify_method": {  # not used
                    "optional": True,
                    "default": "fast-matching",
                    "type": str
                },
                "matching": {
                    "optional": False,
                    "default": ["email"],
                    "type": list
                },
                "sleep_for": {
                    "optional": False,
                    "default": 3600,
                    "type": int
                },
                "database": {
                    "optional": False,
                    "default": "sortinghat_db",
                    "type": str
                },
                "host": {
                    "optional": False,
                    "default": "mariadb",
                    "type": str
                },
                "user": {
                    "optional": False,
                    "default": "root",
                    "type": str
                },
                "password": no_optional_empty_string,
                "autoprofile": {
                    "optional": False,
                    "default": ["customer", "git", "github"],
                    "type": list
                },
                "load_orgs": {
                    "optional": True,
                    "default": False,
                    "type": bool,
                    "deprecated": "Orgs are loaded if defined always"
                },
                "identities_format": {
                    "optional": True,
                    "default": "sortinghat",
                    "type": str,
                    "doc": "Format of the identities data to be loaded"
                },
                "github_api_token": {
                    "optional": True,
                    "default": None,
                    "type": str,
                    "deprecated": "Use identities_api_token"
                },
                "strict_mapping":  {
                    "optional": True,
                    "default": True,
                    "type": bool,
                    "doc": "rigorous check of values in identities matching " + \
                            "(i.e, well formed email addresses)"
                },
                "reset_on_load":  {
                    "optional": True,
                    "default": False,
                    "type": bool,
                    "doc": "Unmerge and remove affiliations for all identities on load"
                },
                "orgs_file": optional_string_none,
                "identities_file": optional_empty_list,
                "identities_export_url": optional_string_none,
                "identities_api_token": optional_string_none,
                "bots_names": optional_empty_list,
                "no_bots_names": optional_empty_list  # to clean bots in SH
            }
        }

        params_track_items = {
            "track_items": {
                "project": {
                    "optional": False,
                    "default": "TrackProject",
                    "type": str
                },
                "upstream_raw_es_url": no_optional_empty_string,
                "raw_index_gerrit": no_optional_empty_string,
                "raw_index_git": no_optional_empty_string
            }
        }

        tasks_config_params = [params_collection, params_enrichment, params_panels,
                               params_report, params_sortinghat, params_track_items]

        for section_params in tasks_config_params:
            params.update(section_params)


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
        # TODO: Return a deepcopy to avoid uncontrolled changes in config?
        return self.conf

    def set_param(self, section, param, value):
        """ Change a param in the config """
        if section not in self.conf or param not in self.conf[section]:
            logger.error('Config section %s and param %s not exists', section, param)
        else:
            self.conf[section][param] = value

    @classmethod
    def get_backend_sections(cls):
        # a backend name could include and extra ":<param>"
        # to have several backend entries with different configs
        gelk_backends = list(get_connectors().keys())
        extra_backends = ["apache", "google_hits", "remo:activities"]

        return gelk_backends + extra_backends

    @classmethod
    def get_global_data_sources(cls):
        """ Data sources than are collected and enriched globally """

        return ['bugzilla', 'bugzillarest', 'confluence', 'discourse', 'gerrit', 'jenkins', 'jira']

    def get_data_sources(self):
        data_sources = []
        backend_sections = self.get_backend_sections()

        for section in self.conf.keys():
            if section in backend_sections:
                data_sources.append(section)

        return data_sources


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
                    else:
                        # Add the default value for this param
                        config[section][param] = check_params[section][param]['default']
                else:
                    ptype = type(config[section][param])
                    ptype_ok = check_params[section][param]["type"]
                    if ptype != ptype_ok:
                        msg = "Wrong type for section param: %s %s %s should be %s" % \
                              (section, param, ptype, ptype_ok)
                        raise RuntimeError(msg)

        # And now the backend_section entries
        # A backend section entry could have specific perceval params which are
        # not checked
        check_params = cls.backend_section_params()
        for section in config.keys():
            # [data_source] or [*data_source]
            if section in backend_sections or section[1:] in backend_sections:
                # backend_section or *backend_section
                for param in check_params:
                    if param not in config[section].keys():
                        if not check_params[param]['optional']:
                            raise RuntimeError("Missing section param:", section, param)
                    else:
                        ptype = type(config[section][param])
                        ptype_ok = check_params[param]["type"]
                        if ptype != ptype_ok:
                            msg = "Wrong type for section param: %s %s %s should be %s" % \
                                  (section, param, ptype, ptype_ok)
                            raise RuntimeError(msg)

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

    def _add_to_conf(self, new_conf):
        """Add new configuration to self.conf.

        Adds configuration parameters in new_con to self.conf.
        If they already existed in conf, overwrite them.

        :param new_conf: new configuration, to add
        """

        for section in new_conf:
            if section not in self.conf:
                self.conf[section] = new_conf[section]
            else:
                for param in new_conf[section]:
                    self.conf[section][param] = new_conf[section][param]

    def __read_conf_files(self):
        logger.debug("Reading conf files")
        self.conf = {}
        for conf_file in self.conf_list:
            logger.debug("Reading conf files: %s", conf_file)
            parser = configparser.ConfigParser()
            parser.read(conf_file)
            raw_conf = {s:dict(parser.items(s)) for s in parser.sections()}
            conf = self.__add_types(raw_conf)
            self._add_to_conf(conf)
        self.check_config(self.conf)
