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

import requests

from mordred.task import Task

logger = logging.getLogger(__name__)

class TaskProjects(Task):
    """ Task to manage the projects config """

    ECLIPSE_PROJECTS_URL = 'http://projects.eclipse.org/json/projects/all'
    projects = {}  # static projects data dict

    def is_backend_task(self):
        return False

    @classmethod
    def get_projects(cls):
        return cls.projects

    @classmethod
    def get_repos_by_backend_section(cls, backend_section):
        """ return list with the repositories for a backend_section """

        repos = []
        backend = Task.get_backend(backend_section)

        projects = TaskProjects.get_projects()

        for pro in projects:
            if backend in projects[pro]:
                repos += projects[pro][backend]

        logger.debug("List of repos for %s: %s", backend_section, repos)

        return repos

    def execute(self):
        config = self.conf
        projects_file = config['projects']['projects_file']

        if config['projects']['load_eclipse']:
            logger.info("Getting Eclipse projects (1 min) from  %s ", self.ECLIPSE_PROJECTS_URL)
            eclipse_projects_resp = requests.get(self.ECLIPSE_PROJECTS_URL)
            eclipse_projects = eclipse_projects_resp.json()
            projects = self.__convert_from_eclipse(eclipse_projects)
            # Create a backup file for current projects_file
            shutil.copyfile(projects_file, projects_file + ".bak")
            logger.info("Writing Eclipse projects to %s ", projects_file)
            with open(projects_file, "w") as fprojects:
                json.dump(projects, fprojects, indent=True)

        logger.info("Reading projects data from  %s ", projects_file)
        with open(projects_file, 'r') as fprojects:
            projects = json.load(fprojects)
        TaskProjects.projects = projects

    def __convert_from_eclipse(self, eclipse_projects):
        """ Convert from eclipse projects format to grimoire projects json format """
        # Extracted from https://github.com/grimoirelab/GrimoireELK/blob/master/mordred/utils/filter_eclipse_projects.py
        output = {"projects":{}}
        tree = eclipse_projects
        count_repos = 0
        for p in tree["projects"]:
            output["projects"][p] = {}

            res_repos = []
            for rep in tree["projects"][p]["source_repo"]:
                url = rep["url"]
                url = url.replace("git.eclipse.org/c/", "git.eclipse.org/gitroot/")
                res_repos.append({"url":url})
            count_repos += len(tree["projects"][p]["source_repo"])
            output["projects"][p]["source_repo"] = []
            output["projects"][p]["git"] = res_repos
            output["projects"][p]["title"] = tree["projects"][p]["title"]
            output["projects"][p]["parent_project"] = tree["projects"][p]["parent_project"]
            output["projects"][p]["bugzilla"] = tree["projects"][p]["bugzilla"]
            output["projects"][p]["mailing_lists"] = tree["projects"][p]["mailing_lists"]
            output["projects"][p]["description"] = tree["projects"][p]["description"]
            output["projects"][p]["dev_list"] = tree["projects"][p]["dev_list"]
            output["projects"][p]["downloads"] = tree["projects"][p]["downloads"]
            output["projects"][p]["wiki_url"] = tree["projects"][p]["wiki_url"]
            output["projects"][p]["forums"] = tree["projects"][p]["forums"]

        logger.debug("Converting project/repos JSON to Grimoire format from Eclipse")
        logger.debug("- %s projects", str(len(tree["projects"])))
        logger.debug("- %s repositories", str(count_repos))

        return output
