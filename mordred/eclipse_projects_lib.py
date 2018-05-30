#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This script manage the information about Eclipse projects
#
# Copyright (C) 2018 Bitergia
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


def compose_mbox(projects):
    """ Compose projects.json only for mbox, but using the mailing_lists lists

    change: 'https://dev.eclipse.org/mailman/listinfo/emft-dev'
    to: 'emfg-dev /home/bitergia/mboxes/emft-dev.mbox/emft-dev.mbox

    :param projects: projects.json
    :return: projects.json with mbox
    """
    mbox_archives = '/home/bitergia/mboxes'

    mailing_lists_projects = [project for project in projects if 'mailing_lists' in projects[project]]
    for mailing_lists in mailing_lists_projects:
        projects[mailing_lists]['mbox'] = []
        for mailing_list in projects[mailing_lists]['mailing_lists']:
            if 'listinfo' in mailing_list:
                name = mailing_list.split('listinfo/')[1]
            elif 'mailing-list' in mailing_list:
                name = mailing_list.split('mailing-list/')[1]
            else:
                name = mailing_list.split('@')[0]

            list_new = "%s %s/%s.mbox/%s.mbox" % (name, mbox_archives, name, name)
            projects[mailing_lists]['mbox'].append(list_new)

    return projects


def compose_gerrit(projects):
    """ Compose projects.json for gerrit, but using the git lists

    change: 'http://git.eclipse.org/gitroot/xwt/org.eclipse.xwt.git'
    to: 'git.eclipse.org_xwt/org.eclipse.xwt

    :param projects: projects.json
    :return: projects.json with gerrit
    """
    git_projects = [project for project in projects if 'git' in projects[project]]
    for project in git_projects:
        repos = [repo for repo in projects[project]['git'] if 'gitroot' in repo]
        if len(repos) > 0:
            projects[project]['gerrit'] = []
        for repo in repos:
            gerrit_project = repo.replace("http://git.eclipse.org/gitroot/", "")
            gerrit_project = gerrit_project.replace(".git", "")
            projects[project]['gerrit'].append("git.eclipse.org_" + gerrit_project)

    return projects


def compose_git(projects, data):
    """ Compose projects.json for git

    We need to replace '/c/' by '/gitroot/' for instance

    change: 'http://git.eclipse.org/c/xwt/org.eclipse.xwt.git'
    to: 'http://git.eclipse.org/gitroot/xwt/org.eclipse.xwt.git'

    :param projects: projects.json
    :param data: eclipse JSON
    :return: projects.json with git
    """
    for p in [project for project in data if len(data[project]['source_repo']) > 0]:
        repos = []
        for url in data[p]['source_repo']:
            if len(url['url'].split()) > 1:  # Error at upstream the project 'tools.corrosion'
                repo = url['url'].split()[1].replace('/c/', '/gitroot/')
            else:
                repo = url['url'].replace('/c/', '/gitroot/')

            if repo not in repos:
                repos.append(repo)

        projects[p]['git'] = repos

    return projects


def compose_mailing_lists(projects, data):
    """ Compose projects.json for mailing lists

    At upstream has two different key for mailing list: 'mailings_lists' and 'dev_list'
    The key 'mailing_lists' is an array with mailing lists
    The key 'dev_list' is a dict with only one mailing list

    :param projects: projects.json
    :param data: eclipse JSON
    :return: projects.json with mailing_lists
    """
    for p in [project for project in data if len(data[project]['mailing_lists']) > 0]:
        if 'mailing_lists' not in projects[p]:
            projects[p]['mailing_lists'] = []

        urls = [url['url'].replace('mailto:', '') for url in data[p]['mailing_lists'] if
                url['url'] not in projects[p]['mailing_lists']]
        projects[p]['mailing_lists'] += urls

    for p in [project for project in data if len(data[project]['dev_list']) > 0]:
        if 'mailing_lists' not in projects[p]:
            projects[p]['mailing_lists'] = []

        mailing_list = data[p]['dev_list']['url'].replace('mailto:', '')
        projects[p]['mailing_lists'].append(mailing_list)

    return projects


def compose_github(projects, data):
    """ Compose projects.json for github

    :param projects: projects.json
    :param data: eclipse JSON
    :return: projects.json with github
    """
    for p in [project for project in data if len(data[project]['github_repos']) > 0]:
        if 'github' not in projects[p]:
            projects[p]['github'] = []

        urls = [url['url'] for url in data[p]['github_repos'] if
                url['url'] not in projects[p]['github']]
        projects[p]['github'] += urls

    return projects


def compose_bugzilla(projects, data):
    """ Compose projects.json for bugzilla

    :param projects: projects.json
    :param data: eclipse JSON
    :return: projects.json with bugzilla
    """
    for p in [project for project in data if len(data[project]['bugzilla']) > 0]:
        if 'bugzilla' not in projects[p]:
            projects[p]['bugzilla'] = []

        urls = [url['query_url'] for url in data[p]['bugzilla'] if
                url['query_url'] not in projects[p]['bugzilla']]
        projects[p]['bugzilla'] += urls

    return projects


def compose_title(projects, data):
    """ Compose the projects JSON file only with the projects name

    :param projects: projects.json
    :param data: eclipse JSON with the origin format
    :return: projects.json with titles
    """
    for project in data:
        projects[project] = {
            'meta': {
                'title': data[project]['title']
            }
        }
    return projects


def compose_projects_json(projects, data):
    """ Compose projects.json with all data sources

    :param projects: projects.json
    :param data: eclipse JSON
    :return: projects.json with all data sources
    """
    projects = compose_git(projects, data)
    projects = compose_mailing_lists(projects, data)
    projects = compose_bugzilla(projects, data)
    projects = compose_github(projects, data)
    projects = compose_gerrit(projects)
    projects = compose_mbox(projects)

    return projects
