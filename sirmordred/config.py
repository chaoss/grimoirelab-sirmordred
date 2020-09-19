#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2019 Bitergia
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
#       Alvaro del Castillo <acs@bitergia.com>
#       Luis Cañas-Díaz <lcanas@bitergia.com>
#       Quan Zhou <quan@bitergia.com>
#       Miguel Ángel Fernández <mafesan@bitergia.com>
#

import configparser
import logging

from sirmordred.task import Task
from grimoire_elk.utils import get_connectors

logger = logging.getLogger(__name__)


MENU_YAML = 'menu.yaml'
ALIASES_JSON = 'aliases.json'
PROJECTS_JSON = 'projects.json'
GLOBAL_DATA_SOURCES = ['bugzilla', 'bugzillarest', 'confluence',
                       'discourse', 'gerrit', 'jenkins', 'jira']


class Config():
    """Class aimed to manage sirmordred configuration"""

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

    @classmethod
    def backend_section_params(self):
        # Params that must exists in all backends
        params = {
            "enriched_index": {
                "optional": False,
                "default": None,
                "type": str,
                "description": "Index name in which to store the enriched items"
            },
            "raw_index": {
                "optional": False,
                "default": None,
                "type": str,
                "description": "Index name in which to store the raw items"
            },
            "studies": {
                "optional": True,
                "default": [],
                "type": list,
                "description": "List of studies to be executed"
            }
        }

        return params

    @classmethod
    def general_params(cls):
        """ Define all the possible config params """

        params = {}

        # GENERAL CONFIG
        params_general = {
            "general": {
                "min_update_delay": {
                    "optional": True,
                    "default": 60,
                    "type": int,
                    "description": "Short delay between tasks (collect, enrich ...)"
                },
                "update": {
                    "optional": False,
                    "default": False,
                    "type": bool,
                    "description": "Execute the tasks in loop"
                },
                "short_name": {
                    "optional": False,
                    "default": "Short name",
                    "type": str,
                    "description": "Short name of the project"
                },
                "debug": {
                    "optional": False,
                    "default": True,
                    "type": bool,
                    "description": "Debug mode (logging mainly)"
                },
                "logs_dir": {
                    "optional": False,
                    "default": "logs",
                    "type": str,
                    "description": "Directory with the logs of sirmordred"
                },
                "bulk_size": {
                    "optional": True,
                    "default": 1000,
                    "type": int,
                    "description": "Number of items to write in Elasticsearch using bulk operations"
                },
                "scroll_size": {
                    "optional": True,
                    "default": 100,
                    "type": int,
                    "description": "Number of items to read from Elasticsearch when scrolling"
                },
                "aliases_file": {
                    "optional": True,
                    "default": ALIASES_JSON,
                    "type": str,
                    "description": "JSON file to define aliases for raw and enriched indexes"
                },
                "menu_file": {
                    "optional": True,
                    "default": MENU_YAML,
                    "type": str,
                    "description": "YAML file to define the menus to be shown in Kibiter"
                },
                "retention_time": {
                    "optional": True,
                    "default": None,
                    "type": int,
                    "description": "The maximum number of minutes wrt the current date to retain the data"
                }
            }
        }
        params_projects = {
            "projects": {
                "projects_file": {
                    "optional": True,
                    "default": PROJECTS_JSON,
                    "type": str,
                    "description": "Projects file path with repositories to be collected group by projects"
                },
                "projects_url": {
                    "optional": True,
                    "default": None,
                    "type": str,
                    "description": "Projects file URL"
                }
            }
        }

        params_phases = {
            "phases": {
                "collection": {
                    "optional": False,
                    "default": True,
                    "type": bool,
                    "description": "Activate collection of items"
                },
                "enrichment": {
                    "optional": False,
                    "default": True,
                    "type": bool,
                    "description": "Activate enrichment of items"
                },
                "identities": {
                    "optional": False,
                    "default": True,
                    "type": bool,
                    "description": "Do the identities tasks"
                },
                "panels": {
                    "optional": False,
                    "default": True,
                    "type": bool,
                    "description": "Load panels, create alias and other tasks related"
                }
            }
        }

        general_config_params = [params_general, params_projects, params_phases]

        for section_params in general_config_params:
            params.update(section_params)

        # Config provided by tasks
        params_collection = {
            "es_collection": {
                "url": {
                    "optional": False,
                    "default": "http://172.17.0.1:9200",
                    "type": str,
                    "description": "Elasticsearch URL"
                }
            }
        }

        params_enrichment = {
            "es_enrichment": {
                "url": {
                    "optional": False,
                    "default": "http://172.17.0.1:9200",
                    "type": str,
                    "description": "Elasticsearch URL"
                },
                "autorefresh": {
                    "optional": True,
                    "default": True,
                    "type": bool,
                    "description": "Execute the autorefresh of identities"
                },
                "autorefresh_interval": {
                    "optional": True,
                    "default": 2,
                    "type": int,
                    "description": "Set time interval (days) for autorefresh identities"
                }
            }
        }

        params_panels = {
            "panels": {
                "strict": {
                    "optional": True,
                    "default": True,
                    "type": bool,
                    "description": "Enable strict panels loading"
                },
                "kibiter_time_from": {
                    "optional": True,
                    "default": "now-90d",
                    "type": str,
                    "description": "Default time interval for Kibiter"
                },
                "kibiter_default_index": {
                    "optional": True,
                    "default": "git",
                    "type": str,
                    "description": "Default index pattern for Kibiter"
                },
                "kibiter_url": {
                    "optional": False,
                    "default": None,
                    "type": str,
                    "description": "Kibiter URL"
                },
                "kibiter_version": {
                    "optional": True,
                    "default": None,
                    "type": str,
                    "description": "Kibiter version"
                },
                "community": {
                    "optional": True,
                    "default": True,
                    "type": bool,
                    "description": "Enable community structure menu"
                },
                "kafka": {
                    "optional": True,
                    "default": False,
                    "type": bool,
                    "description": "Enable kafka menu"
                },
                "github-comments": {
                    "optional": True,
                    "default": False,
                    "type": bool,
                    "description": "Enable GitHub comments menu"
                },
                "github-events": {
                    "optional": True,
                    "default": False,
                    "type": bool,
                    "description": "Enable GitHub events menu"
                },
                "github-repos": {
                    "optional": True,
                    "default": False,
                    "type": bool,
                    "description": "Enable GitHub repo stats menu"
                },
                "gitlab-issues": {
                    "optional": True,
                    "default": False,
                    "type": bool,
                    "description": "Enable GitLab issues menu"
                },
                "gitlab-merges": {
                    "optional": True,
                    "default": False,
                    "type": bool,
                    "description": "Enable GitLab merge requests menu"
                },
                "mattermost": {
                    "optional": True,
                    "default": False,
                    "type": bool,
                    "description": "Enable Mattermost menu"
                },
                "code-license": {
                    "optional": True,
                    "default": False,
                    "type": bool,
                    "description": "Enable Code License menu"
                },
                "code-complexity": {
                    "optional": True,
                    "default": False,
                    "type": bool,
                    "description": "Enable Code Complexity menu"
                },
                "contact": {
                    "optional": True,
                    "default": None,
                    "type": str,
                    "description": "Support repository URL"
                }
            }
        }

        params_sortinghat = {
            "sortinghat": {
                "affiliate": {
                    "optional": False,
                    "default": "True",
                    "type": bool,
                    "description": "Affiliate identities to organizations"
                },
                "unaffiliated_group": {
                    "optional": False,
                    "default": "Unknown",
                    "type": str,
                    "description": "Name of the organization for unaffiliated identities"
                },
                "matching": {
                    "optional": False,
                    "default": ["email"],
                    "type": list,
                    "description": "Algorithm for matching identities in Sortinghat"
                },
                "sleep_for": {
                    "optional": False,
                    "default": 3600,
                    "type": int,
                    "description": "Delay between task identities executions"
                },
                "database": {
                    "optional": False,
                    "default": "sortinghat_db",
                    "type": str,
                    "description": "Name of the Sortinghat database"
                },
                "host": {
                    "optional": False,
                    "default": "mariadb",
                    "type": str,
                    "description": "Host with the Sortinghat database"
                },
                "user": {
                    "optional": False,
                    "default": "root",
                    "type": str,
                    "description": "User to access the Sortinghat database"
                },
                "password": {
                    "optional": False,
                    "default": "",
                    "type": str,
                    "description": "Password to access the Sortinghat database"
                },
                "autoprofile": {
                    "optional": False,
                    "default": ["customer", "git", "github"],
                    "type": list,
                    "description": "Order in which to get the identities information for filling the profile"
                },
                "load_orgs": {
                    "optional": True,
                    "default": False,
                    "type": bool,
                    "deprecated": "Load organizations in Sortinghat database",
                    "description": ""
                },
                "identities_format": {
                    "optional": True,
                    "default": "sortinghat",
                    "type": str,
                    "description": "Format of the identities data to be loaded"
                },
                "strict_mapping": {
                    "optional": True,
                    "default": True,
                    "type": bool,
                    "description": "rigorous check of values in identities matching "
                                   "(i.e, well formed email addresses)"
                },
                "reset_on_load": {
                    "optional": True,
                    "default": False,
                    "type": bool,
                    "description": "Unmerge and remove affiliations for all identities on load"
                },
                "orgs_file": {
                    "optional": True,
                    "default": None,
                    "type": str,
                    "description": "File path with the organizations to be loaded in Sortinghat"
                },
                "identities_file": {
                    "optional": True,
                    "default": [],
                    "type": list,
                    "description": "File path with the identities to be loaded in Sortinghat"
                },
                "identities_export_url": {
                    "optional": True,
                    "default": None,
                    "type": str,
                    "description": "URL in which to export the identities in Sortinghat"
                },
                "identities_api_token": {
                    "optional": True,
                    "default": None,
                    "type": str,
                    "description": "API token for remote operation with GitHub and Gitlab"
                },
                "autogender": {
                    "optional": True,
                    "default": False,
                    "type": bool,
                    "description": "Add gender to the profiles (executes autogender)"
                }
            }
        }

        tasks_config_params = [params_collection, params_enrichment, params_panels, params_sortinghat]
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
                    val = section_name + "-raw"
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
        extra_backends = ["apache"]

        return gelk_backends + extra_backends

    @classmethod
    def get_study_sections(cls):
        # a study name could include and extra ":<param>"
        # to have several backend entries with different configs
        studies = ("enrich_demography", "enrich_areas_of_code", "enrich_onion", "kafka_kip",
                   "enrich_pull_requests", "enrich_git_branches", "enrich_cocom_analysis",
                   "enrich_colic_analysis", "enrich_geolocation", "enrich_forecast_activity",
                   "enrich_extra_data", "enrich_feelings", "enrich_backlog_analysis",
                   "enrich_duration_analysis", "enrich_demography_contribution",
                   "enrich_reference_analysis")

        return studies

    def get_active_data_sources(self):
        data_sources = []
        backend_sections = self.get_backend_sections()

        for section in self.conf.keys():
            data_source = section.split(":")[0]
            if data_source in backend_sections:
                data_sources.append(data_source)

        return data_sources

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
        study_sections = cls.get_study_sections()

        # filter out commented sections (e.g., [*backend_section:tag])
        config_sections = [section for section in config.keys() if section.split(":")[0][0] != "*"]

        for section in config_sections:
            if Task.get_backend(section) in backend_sections:
                # backend_section:tag
                continue
            if section.startswith((study_sections)):
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
                    ptype_default = check_params[section][param]["default"]
                    if ptype != ptype_ok and ptype_default is not None:
                        msg = "Wrong type for section param: %s %s %s should be %s" % \
                              (section, param, ptype, ptype_ok)
                        raise RuntimeError(msg)

        # And now the backend_section entries
        # A backend section entry could have specific perceval params which are
        # not checked
        check_params = cls.backend_section_params()
        for section in config_sections:
            if Task.get_backend(section) in backend_sections:
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
                if len(val) > 1 and (val[0] == '"' and val[-1] == '"'):
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
                elif val.lower() == 'none':
                    typed_conf[s][option] = ''
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
            raw_conf = {s: dict(parser.items(s)) for s in parser.sections()}
            conf = self.__add_types(raw_conf)
            self._add_to_conf(conf)
        self.check_config(self.conf)
