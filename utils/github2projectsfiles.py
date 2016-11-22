#!/usr/bin/python
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
#   Quan Zhou <quan@bitergia.com>
#


import argparse
import requests
import sys
import yaml


GITHUB_API_URL = "https://api.github.com/"


def open_file(file_name, opt):
    if opt == "yml":
        try:
            with open(file_name, 'r') as f:
                data = yaml.load(f)
        except:
            data = {}

        return data

    elif opt == "blacklist":
        try:
            lines = [line.rstrip('\n') for line in open(filename)]
        except:
            sys.exit("Blacklist file doesn't exist")

        return lines

def write_yaml(file_name, data):
    with open(file_name, 'w+') as f:
        noalias_dumper = yaml.dumper.SafeDumper
        noalias_dumper.ignore_aliases = lambda self, data: True
        yaml.dump(data, f, default_flow_style=False, Dumper=noalias_dumper)

def read_arguments():
    desc="Get the repositories for a Github organization and return hierarchy.yml and porjects-repos.yml"
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=desc)

    parser.add_argument("--h",
                        action="store",
                        dest="hierarchy",
                        help="The name of the hierarchy file, by default is hierarchy.yml")
    parser.add_argument("--r",
                        action="store",
                        dest="repo",
                        help="The name of the project repos file, by default is project_repos.yml")
    parser.add_argument("org",
                        action="store",
                        help="Github organization")
    parser.add_argument("-p","--parent",
                        action="store",
                        dest="parent",
                        help="Parent project, if you give parent value null, it will go to the root")
    parser.add_argument("-b","--blacklist",
                        action="store",
                        dest="blacklist",
                        help="Blacklist of repos")
    parser.add_argument("-r","--rename",
                        action="store",
                        dest="rename",
                        help="Give a specifty name for this github organization")

    args = parser.parse_args()

    return args

def get_repo_url(user, blacklist):
    git = []
    names = []

    url = GITHUB_API_URL+"users/"+user+"/repos"

    page = 0
    last_page = 0

    r = requests.get(url+"?page="+str(page))
    r.raise_for_status()

    for repo in r.json():
        if repo['html_url'] not in blacklist and not repo['fork']:
            git.append(repo['clone_url'])
            names.append(repo['name'])

    if 'last' in r.links:
        last_url = r.links['last']['url']
        last_page = last_url.split('page=')[1]
        last_page = int(last_page)

    while(page < last_page):
        page += 1
        r = requests.get(url+"?page="+str(page))
        r.raise_for_status()

        for repo in r.json():
            if repo['html_url'] not in blacklist and not repo['fork']:
                git.append(repo['clone_url'])
                names.append(repo['name'])

    return git, names

def add(key, values, lists,):
    lists[key] = []
    for value in values:
        lists[key].append({value: []})

    return lists

def search_child(hierarchy, org, delete=True, subproj=None):
    old_parent = {}
    if org in hierarchy:
        old_parent[org] = hierarchy[org]
        if delete:
            hierarchy.pop(org, None)

        return old_parent

    else:
        for orgs in hierarchy:
            aux_hierarchy = {}
            if type(hierarchy) == dict:
                aux_hierarchy = hierarchy[orgs]
            elif type(hierarchy) == list and type(orgs) != str:
                i = hierarchy.index(orgs)
                for key in hierarchy[i]:
                    if key == org:
                        proj = hierarchy[i]
                        if subproj:
                            add(key, subprojects, hierarchy[i])
                        elif delete:
                            del hierarchy[i]
                        return proj
                    else:
                        aux_hierarchy = hierarchy[i][key]

            if len(aux_hierarchy) != 0:
                parent = search_child(aux_hierarchy, org, delete, subproj)
                if parent != None:
                    return parent

def add_parent(hierarchy, parent, child):
    if parent in hierarchy:
        hierarchy[parent].append(child)
        return hierarchy
    else:
        for org in hierarchy:
            aux_hierarchy = {}
            if type(hierarchy) == dict:
                aux_hierarchy = hierarchy[org]
            elif type(hierarchy) == list and type(org) != str:
                i = hierarchy.index(org)
                aux_hierarchy = hierarchy[i]
            aux = add_parent(aux_hierarchy, parent, child)
            if aux != None:
                return hierarchy

def add_projects(repos, projects_repos, org, name):
    projects_repos[name] = {
        "meta": {
            "title": org.lower()
        },
        "github": "https://github.com/"+org
    }

    for repo in repos:
        name = repo.split("https://github.com/")[1].split("/")[1].split(".git")[0]
        github = repo.split(".git")[0]
        projects_repos[name] = {
            "meta": {
                "title": name.lower()
            },
            "git": repo,
            "github": github
        }

    return projects_repos

if __name__ == "__main__":
    args = read_arguments()

    hierarchy_name = "hierarchy.yml"
    if args.hierarchy:
        hierarchy_name = args.hierarchy
    hierarchy = open_file(hierarchy_name, "yml")

    projects_repos_name = "project_repos.yml"
    if args.repo:
        projects_repos_name = args.repo
    projects_repos = open_file(projects_repos_name, "yml")

    org = args.org

    name = org
    if args.rename:
        name = args.rename

    blacklist = []
    if args.blacklist:
        blacklist = open_file(args.blacklist, "blacklist")

    repos, subprojects = get_repo_url(org, blacklist)

    if len(hierarchy) == 0:
        hierarchy = add(name, subprojects, hierarchy)
    else:
        found = search_child(hierarchy, name, delete=False, subproj=subprojects)
        if found == None:
            hierarchy = add(name, subprojects, hierarchy)

    if args.parent:
        parent = args.parent
        if (parent == name):
            sys.exit("The parent name and the organization name must be different "+parent)

        r = requests.get("https://github.com/"+parent)
        r.raise_for_status()

        child = search_child(hierarchy, name)
        if child == None:
            child = {name: []}
        if parent == "null":
            hierarchy.update(child)
        else:
            hierarchy_aux = add_parent(hierarchy, parent, child)
            if hierarchy_aux == None:
                hierarchy[parent] = [child]
            else:
                hierarchy = hierarchy_aux

    else:
        found = search_child(hierarchy, name, delete=False)
        if found == None:
            hierarchy[name] = []

    write_yaml(hierarchy_name, hierarchy)

    projects_repos = add_projects(repos, projects_repos, org, name)

    write_yaml(projects_repos_name, projects_repos)
