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
#     Quan Zhou <quan@bitergia.com>
#

import json
import logging

from threading import Lock

import requests

from copy import deepcopy

from sirmordred.task import Task
from sirmordred.eclipse_projects_lib import compose_title, compose_projects_json

logger = logging.getLogger(__name__)


class TaskProjects(Task):
    """ Task to manage the projects config """

    GLOBAL_PROJECT = 'unknown'  # project to download and enrich full sites
    __projects = {}  # static projects data dict
    projects_last_diff = []  # Projects changed in last update
    projects_lock = Lock()

    def is_backend_task(self):
        return False

    @classmethod
    def get_projects(cls):
        with cls.projects_lock:
            # Return a deepcopy so it is not changed
            return deepcopy(cls.__projects)

    @classmethod
    def set_projects(cls, projects):
        with cls.projects_lock:
            old_projects_set = set(cls.__projects.keys())
            new_projects_set = set(projects.keys())
            cls.projects_last_diff = list(old_projects_set ^ new_projects_set)
            logger.debug("Update project diff %s", cls.projects_last_diff)
            cls.__projects = projects

    @classmethod
    def get_projects_last_diff(cls):
        return cls.projects_last_diff

    @classmethod
    def get_repos_by_backend_section(cls, backend_section, raw=True):
        """ return list with the repositories for a backend_section """
        repos = []
        projects = TaskProjects.get_projects()

        for pro in projects:
            if backend_section in projects[pro]:
                # if the projects.json doesn't contain the `unknown` project, add the repos in the bck section
                if cls.GLOBAL_PROJECT not in projects:
                    repos += projects[pro][backend_section]
                else:
                    # if the projects.json contains the `unknown` project
                    # in the case of the collection phase
                    if raw:
                        # if the current project is not `unknown`
                        if pro != cls.GLOBAL_PROJECT:
                            # if the bck section is not in the `unknown` project, add the repos in the bck section
                            if backend_section not in projects[cls.GLOBAL_PROJECT]:
                                repos += projects[pro][backend_section]
                            # if the backend section is in the `unknown` project,
                            # add the repo in the bck section under `unknown`
                            elif backend_section in projects[pro] and backend_section in projects[cls.GLOBAL_PROJECT]:
                                repos += projects[cls.GLOBAL_PROJECT][backend_section]
                        # if the current project is `unknown`
                        else:
                            # if the backend section is only in the `unknown` project,
                            # add the repo in the bck section under `unknown`
                            not_in_unknown = [projects[pro] for pro in projects if pro != cls.GLOBAL_PROJECT][0]
                            if backend_section not in not_in_unknown:
                                repos += projects[cls.GLOBAL_PROJECT][backend_section]
                    # in the case of the enrichment phase
                    else:
                        # if the current project is not `unknown`
                        if pro != cls.GLOBAL_PROJECT:
                            # if the bck section is not in the `unknown` project, add the repos in the bck section
                            if backend_section not in projects[cls.GLOBAL_PROJECT]:
                                repos += projects[pro][backend_section]
                            # if the backend section is in the `unknown` project, add the repos in the bck section
                            elif backend_section in projects[pro] and backend_section in projects[cls.GLOBAL_PROJECT]:
                                repos += projects[pro][backend_section]
                        # if the current project is `unknown`
                        else:
                            # if the backend section is only in the `unknown` project,
                            # add the repo in the bck section under `unknown`
                            not_in_unknown_prj = [projects[prj] for prj in projects if prj != cls.GLOBAL_PROJECT]
                            not_in_unknown_sections = list(set([section for prj in not_in_unknown_prj
                                                                for section in list(prj.keys())]))
                            if backend_section not in not_in_unknown_sections:
                                repos += projects[pro][backend_section]

        logger.debug("List of repos for %s: %s (raw=%s)", backend_section, repos, raw)

        # avoid duplicated repos
        repos = list(set(repos))

        return repos

    def execute(self):
        config = self.conf

        if config['projects']['load_eclipse']:
            self.__get_eclipse_projects()
        if config['projects']['projects_url']:
            projects = self.__get_projects_from_url()
        else:
            projects_file = config['projects']['projects_file']
            logger.info("Reading projects data from  %s ", projects_file)
            with open(projects_file, 'r') as fprojects:
                projects = json.load(fprojects)

        TaskProjects.set_projects(projects)

    def __get_projects_from_url(self):
        config = self.conf
        projects_url = config['projects']['projects_url']
        projects_file = config['projects']['projects_file']

        logger.info("Getting projects file from URL: %s ", projects_url)
        res = requests.get(projects_url)
        res.raise_for_status()
        projects = res.json()
        with open(projects_file, "w") as fprojects:
            json.dump(projects, fprojects, indent=True)

        return projects

    def __get_eclipse_projects(self):
        config = self.conf
        projects_file = config['projects']['projects_file']

        eclipse_projects_url = 'http://projects.eclipse.org/json/projects/all'

        logger.info("Getting Eclipse projects (1 min) from  %s ", eclipse_projects_url)
        eclipse_projects_resp = requests.get(eclipse_projects_url)
        eclipse_projects_resp.raise_for_status()
        eclipse_projects = eclipse_projects_resp.json()['projects']
        projects = self.convert_from_eclipse(eclipse_projects)

        with open(projects_file, "w") as fprojects:
            json.dump(projects, fprojects, indent=True)

    def convert_from_eclipse(self, eclipse_projects):
        """ Convert from eclipse projects format to grimoire projects json format """

        projects = {}

        # We need the global project for downloading the full Bugzilla and Gerrit
        projects['unknown'] = {
            "gerrit": ["git.eclipse.org"],
            "bugzilla": ["https://bugs.eclipse.org/bugs/"]
        }

        projects = compose_title(projects, eclipse_projects)
        projects = compose_projects_json(projects, eclipse_projects)

        return projects
