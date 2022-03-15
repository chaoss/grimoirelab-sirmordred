#!/usr/bin/python
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
#   Quan Zhou <quan@bitergia.com>
#


import argparse
import json
import yaml


def write_yaml(file_name, data):
    with open(file_name, 'w+') as f:
        yaml.dump(data, f, default_flow_style=False)


def open_file(file_name):
    data = open(file_name).read()
    json_data = json.loads(data)

    return json_data


def read_arguments():
    desc = "Convert JSON to YML: return hierarchy.yml and projects_repo.yml"
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=desc)

    parser.add_argument("json_file",
                        action="store",
                        help="JSON file: input")

    args = parser.parse_args()

    return args


def get_hierarchy_list(json_data):
    hierarchy_list = {}
    for data in json_data["projects"]:
        if len(json_data["projects"][data]['parent_project']) == 0:
            hierarchy_list[data] = []
        else:
            for key in json_data["projects"][data]['parent_project']:
                hierarchy_list[data][key] = []

    return hierarchy_list


def get_repo_list(json_data, not_backend, special_backend):
    repo_to_return = {}
    for data in json_data["projects"]:
        repo_to_return[data] = {"meta": {"title": json_data["projects"][data]["title"].lower()}}
        for backend_name in json_data["projects"][data]:
            backend = json_data["projects"][data][backend_name]

            if len(backend) > 0 and backend_name not in not_backend or backend_name == "gerrit_repo" and len(backend[0]) > 0:
                repo_list = []
                for repo in backend:
                    if backend_name not in special_backend:
                        repo_list.append(repo['url'])
                    else:
                        repo_list.append(repo['url'] + " " + repo['path'])
                repo_to_return[data][backend_name] = repo_list

    return repo_to_return


if __name__ == "__main__":
    args = read_arguments()
    json_file = args.json_file
    json_data = open_file(json_file)

    not_backend = ["title", "description", "dev_list", "gerrit_repo"]
    special_backend = ["irc", "supybot", "mbox"]

    hierarchy_list = get_hierarchy_list(json_data)
    repo_list = get_repo_list(json_data, not_backend, special_backend)

    write_yaml("hierarchy.yml", hierarchy_list)
    write_yaml("projects-repos.yml", repo_list)
