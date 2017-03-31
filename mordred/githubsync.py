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
#   Quan Zhou <quan@bitergia.com>
#


import json
import os
import requests
import subprocess


GITHUB_API_URL = "https://api.github.com"


class GitHubSync:
    """ Update git and github the file projects.json with github uri. """

    def __init__(self, token):
        self.token = token

    def __get_headers(self):
        if self.token:
            headers = {'Authorization': 'token ' + self.token}
            return headers

    def write_file(self, filename, data):
        with open(filename, 'w+') as f:
            json.dump(data, f, sort_keys=True, indent=4)

    def get_url(self, uri):
        """ Get the github URL from github URI """

        if self.token == "":
            self.token = uri.split("token=")[1]

        uri_path = uri.split("/")
        url = "https://"+uri_path[3]+":"+self.token+"@github.com/"+uri_path[3]+"/"+uri_path[4]+".git"

        return url

    def add_repo(self, git, github, r, fork):
        """ Add html_url and clone_url from a github project only if is new.

        :param git: list clone_url
        :param github: list html_url
        :param r: requests
        :param fork: If fork is true, include the fork repositories

        :returns: Two list git and github repositories
        """

        for repo in r.json():
            if repo['html_url'] not in github:
                if not fork:
                    if not repo['fork']:
                        github.append(repo['html_url'])
                        git.append(repo['clone_url'])
                else:
                    github.append(repo['html_url'])
                    git.append(repo['clone_url'])

        return git, github

    def get_repo(self, project, fork):
        """ Get all html_url and clone_url from a github project.

        :param fork: If fork is true, include the fork repositories

        :returns: Two list git and github repositories
        """

        git = []
        github = []

        url = GITHUB_API_URL+"/users/"+project+"/repos"
        page = 1
        last_page = 0

        r = requests.get(url+"?page="+str(page),
                         headers=self.__get_headers())
        r.raise_for_status()

        git, github = self.add_repo(git, github, r, fork)

        if 'last' in r.links:
            last_url = r.links['last']['url']
            last_page = last_url.split('page=')[1]
            last_page = int(last_page)

        while(page < last_page):
            page += 1
            r = requests.get(url+"?page="+str(page),
                             headers=self.__get_headers())
            r.raise_for_status()

            git, github = self.add_repo(git, github, r, fork)

        return git, github

    def update_json(self, project, projects_file, repo_type, repo_list):
        """ Update the JSON file with the new repositories.

        :param project: The name of the project to update
        :param projects_file: projects.json to update
        :param repos: git or github
        :param repo_list: The new list to update

        :returns: The projects.json with new repositories
        """

        # Check if the repositories exists
        for repo in projects_file[project][repo_type]:
            r = requests.get(repo)
            if r.status_code != 200:
                projects_file[project][repo_type].remove(repo)

        # Add new repositories
        for repo in repo_list:
            if repo not in projects_file[project][repo_type]:
                projects_file[project][repo_type].append(repo)

        return projects_file

    def is_github_uri(self, uri):
        """ Check if the uri is valid.

        :param uri: Github uri URL

        :returns: True if the uri is a valid github url
        """

        r = requests.get(uri)
        status = r.status_code

        if status == 200:
            return True
        else:
            return False

    def load_projects(self, uri):
        """ Load projects.json.

        :param uri: Github uri URL

        :returns: The dict after loading the projects.json file
        """

        r = requests.get(uri,
                         headers=self.__get_headers())
        r.raise_for_status()

        return r.json()

    def sync_with_org(self, projects_file, project, fork=False):
        """ Update the list of project with organizations.

        :param projects_file: projects.json to update
        :param project: Github project name
        :param fork: If fork is true, include the fork repositories

        :returns: the list of projects updated
        """

        git_list, github_list = self.get_repo(project, fork)

        if project in projects_file:
            projects_file = self.update_json(project, projects_file, "git", git_list)
            projects_file = self.update_json(project, projects_file, "github", github_list)

        else:
            new_project = {
                            "meta": {
                                "title": project.lower()
                            }
                          }
            projects_file[project] = new_project
            projects_file[project]["git"] = git_list
            projects_file[project]["github"] = github_list

        return projects_file

    def sync(self, projects_file, project, fork=False):
        """ Update the list of project.

        :param projects_file: projects.json to update
        :param project: Github project name
        :param fork: If fork is true, include the fork repositories

        :returns: the list of projects updated
        """

        git_list, github_list = self.get_repo(project, fork)

        new_project = {
                        "meta": {
                            "title": project.lower()
                        }
                      }
        projects_file[project] = new_project
        projects_file[project]["git"] = git_list
        projects_file[project]["github"] = github_list

        return projects_file

    def push_projects_file(self, uri, projects_file):
        """ Commiting new JSON files with git.

        :param uri: Github uri URL
        :param projects_file: projects.json to update
        """

        url_git = self.get_url(uri)

        destination = "./githubsync/"

        fd = open("githubsync.log", 'w+')

        pr = subprocess.Popen(['/usr/bin/git', 'clone', url_git, "githubsync"],
                              stdout=fd,
                              stderr=fd,
                              shell=False)
        (out, error) = pr.communicate()

        self.write_file(destination+"projects.json", projects_file)

        pr = subprocess.Popen(['/usr/bin/git', 'add', 'projects.json'],
                              cwd=os.path.dirname(destination),
                              stdout=fd,
                              stderr=fd,
                              shell=False)
        (out, error) = pr.communicate()

        pr = subprocess.Popen(['/usr/bin/git', 'commit', '-m', 'projects.json updated by the Owl Bot'],
                              cwd=os.path.dirname(destination),
                              stdout=fd,
                              stderr=fd,
                              shell=False)
        (out, error) = pr.communicate()

        pr = subprocess.Popen(['/usr/bin/git', 'push', 'origin', 'master'],
                              cwd=os.path.dirname(destination),
                              stdout=fd,
                              stderr=fd,
                              shell=False)
        (out, error) = pr.communicate()

        pr = subprocess.Popen(['rm', '-rf', 'githubsync'],
                              stdout=fd,
                              stderr=fd,
                              shell=False)
        (out, error) = pr.communicate()

        fd.close()
