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

import json
import logging
import shutil

from threading import Lock
from os import path

import requests

from copy import deepcopy

from mordred.config import Config
from mordred.task import Task
from mordred.eclipse_projects_lib import get_repos_list_project, get_mls_repos



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
    def get_repos_by_backend_section(cls, backend_section):
        """ return list with the repositories for a backend_section """
        repos = []
        backend = Task.get_backend(backend_section)

        projects = TaskProjects.get_projects()

        for pro in projects:
            if backend in projects[pro]:
                if backend in Config.get_global_data_sources() \
                    and cls.GLOBAL_PROJECT in projects and pro != cls.GLOBAL_PROJECT:
                    logger.debug("Skip global data source %s for project %s",
                                 backend, pro)
                else:
                    repos += projects[pro][backend]

        logger.debug("List of repos for %s: %s", backend_section, repos)

        return repos

    def execute(self):
        config = self.conf
        projects_file = config['projects']['projects_file']

        if config['projects']['load_eclipse']:
            self.__get_eclipse_projects()

        logger.info("Reading projects data from  %s ", projects_file)
        with open(projects_file, 'r') as fprojects:
            projects = json.load(fprojects)
        TaskProjects.set_projects(projects)

    def __get_eclipse_projects(self):
        config = self.conf
        projects_file = config['projects']['projects_file']

        eclipse_projects_url = 'http://projects.eclipse.org/json/projects/all'
        # For debugging with a Eclipse local file
        eclipse_projects_file = 'VizGrimoireUtils/eclipse/http:__projects.eclipse.org_json_projects_all.json'

        logger.info("Getting Eclipse projects (1 min) from  %s ", eclipse_projects_url)
        eclipse_projects_resp = requests.get(eclipse_projects_url)
        eclipse_projects = eclipse_projects_resp.json()['projects']
        projects = self.convert_from_eclipse(eclipse_projects)

        # Create a backup file for current projects_file
        if path.isfile(projects_file):
            shutil.copyfile(projects_file, projects_file + ".bak")
        logger.info("Writing Eclipse projects to %s ", projects_file)
        with open(projects_file, "w") as fprojects:
            json.dump(projects, fprojects, indent=True)

    def __convert_eclipse_mls(self, mls_data):
        """ We need to convert:

        [
         "https://dev.eclipse.org/mailman/listinfo/sisu-dev",
         "https://dev.eclipse.org/mailman/listinfo/sisu-users"
        ]

        to

        [
            "sisu-users /home/bitergia/mboxes/sisu-users.mbox/sisu-users.mbox",
            "sisu-dev /home/bitergia/mboxes/sisu-dev.mbox/sisu-dev.mbox"
        ]

        """

        mbox_archives = '/home/bitergia/mboxes'
        mls = []

        for mlist in mls_data:
            if len(mlist.rsplit("/", 1)) != 2:
                logger.warning("Wrong list format %s", mlist)
                continue
            name = mlist.rsplit("/", 1)[1]
            list_new = "%s %s/%s.mbox/%s.mbox" % (name, mbox_archives, name, name)
            mls.append(list_new)

        return mls


    def convert_from_eclipse(self, eclipse_projects):
        """ Convert from eclipse projects format to grimoire projects json format """

        projects = {}

        # We need the global project for downloading the full Bugzilla and Gerrit
        projects['unknown'] = {
            "gerrit": ["git.eclipse.org"],
            "bugzilla": ["https://bugs.eclipse.org/bugs/"]
        }

        for project in eclipse_projects:
            projects[project] = {}
            pdata = projects[project]
            pdata["meta"] = {
                "title": eclipse_projects[project]["title"]
            }
            pdata["git"] = get_repos_list_project(project, eclipse_projects, "scm")
            pdata["bugzilla"] = get_repos_list_project(project, eclipse_projects, "its")
            pdata["mailing_lists"] = get_mls_repos(eclipse_projects[project], True)
            pdata["mbox"] = self.__convert_eclipse_mls(pdata["mailing_lists"])
            pdata["gerrit"] = get_repos_list_project(project, eclipse_projects, "scr", 'git.eclipse.org')
            # pdata["irc"] = get_repos_list_project(project, eclipse_projects, "irc")

        return projects
