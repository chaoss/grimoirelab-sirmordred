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
import sys
import unittest

import httpretty
import requests

sys.path.insert(0, '..')

from mordred.githubsync import GitHubSync


GITHUB_URL = "https://github.com/"
GITHUB_API_URL = "https://api.github.com/users/zhquan_example/repos"
URI = "https://raw.githubusercontent.com/zhquan_example/project/projects.json"
TOKEN = "mytoken"


class TestGitHubSync(unittest.TestCase):

    @httpretty.activate
    def test_is_github_uri(self):
        """ Test if URI is valid. """

        json_uri = {
            "uri": {
                "git": [
                    "https://github.com/uri/project_1.git",
                    "https://github.com/uri/project_2.git"
                ],
                "github": [
                    "https://github.com/uri/project_1",
                    "https://github.com/uri/project_2"
                ],
                "meta": {
                    "title": "uri"
                }
            }
        }

        httpretty.register_uri(httpretty.GET,
                               URI,
                               body=json.dumps(json_uri),
                               status=200)

        github = GitHubSync(TOKEN)

        self.assertTrue(github.is_github_uri(URI))

    @httpretty.activate
    def test_sync_with_org(self):
        """ Test updated projects.json with URI. """

        json_uri = {
            "uri": {
                "git": [
                    "https://github.com/uri/project_1.git",
                    "https://github.com/uri/project_2.git"
                ],
                "github": [
                    "https://github.com/uri/project_1",
                    "https://github.com/uri/project_2"
                ],
                "meta": {
                    "title": "uri"
                }
            }
        }
        api_page_1 = [
            {
                "id": 1,
                "name": "project_1",
                "full_name": "zhquan_example/project_1",
                "html_url": "https://github.com/zhquan_example/project_1",
                "clone_url": "https://github.com/zhquan_example/project_1.git",
                "fork": False
            },
            {
                "id": 2,
                "name": "project_2",
                "full_name": "zhquan_example/project_2",
                "html_url": "https://github.com/zhquan_example/project_2",
                "clone_url": "https://github.com/zhquan_example/project_2.git",
                "fork": False
            }
        ]
        api_page_2 = [
            {
                "id": 3,
                "name": "project_3",
                "full_name": "zhquan_example/project_3",
                "html_url": "https://github.com/zhquan_example/project_3",
                "clone_url": "https://github.com/zhquan_example/project_3.git",
                "fork": True
            },
            {
                "id": 4,
                "name": "project_4",
                "full_name": "zhquan_example/project_4",
                "html_url": "https://github.com/zhquan_example/project_4",
                "clone_url": "https://github.com/zhquan_example/project_4.git",
                "fork": False
            },
            {
                "id": 5,
                "name": "project_5",
                "full_name": "zhquan_example/project_5",
                "html_url": "https://github.com/zhquan_example/project_5",
                "clone_url": "https://github.com/zhquan_example/project_5.git",
                "fork": False
            }
        ]
        httpretty.register_uri(httpretty.GET,
                               URI,
                               body=json.dumps(json_uri),
                               status=200)
        httpretty.register_uri(httpretty.GET,
                               GITHUB_API_URL+"?page=1",
                               body=json.dumps(api_page_1),
                               status=200,
                               forcing_headers={
                                    'Link': '<' + GITHUB_API_URL + '/?&page=2>; rel="next", <' +
                                       GITHUB_API_URL + '/?&page=2>; rel="last"'
                               })
        httpretty.register_uri(httpretty.GET,
                               GITHUB_API_URL+"?page=2",
                               body=json.dumps(api_page_2),
                               status=200,
                               forcing_headers={
                                    'Link': '<' + GITHUB_API_URL + '/?&page=2>; rel="next", <' +
                                       GITHUB_API_URL + '/?&page=2>; rel="last"'
                               })

        json_expected = {
            "zhquan_example": {
                "git": [
                    "https://github.com/zhquan_example/project_4.git",
                    "https://github.com/zhquan_example/project_1.git",
                    "https://github.com/zhquan_example/project_2.git"
                ],
                "github": [
                    "https://github.com/zhquan_example/project_4",
                    "https://github.com/zhquan_example/project_1",
                    "https://github.com/zhquan_example/project_2"
                ],
                "meta": {
                    "title": "zhquan_example"
                }
            },
            "uri": {
                "git": [
                    "https://github.com/uri/project_1.git",
                    "https://github.com/uri/project_2.git"
                ],
                "github": [
                    "https://github.com/uri/project_1",
                    "https://github.com/uri/project_2"
                ],
                "meta": {
                    "title": "uri"
                }
            }
        }

        blacklist = ["project_5"]
        github = GitHubSync(TOKEN)
        projects = github.load_projects(URI)
        projects = github.sync_with_org(projects, "zhquan_example", blacklist=blacklist)

        self.assertDictEqual(json_expected, projects)

        expected = {
            'page': ['2']
        }
        self.assertDictEqual(httpretty.last_request().querystring, expected)

    @httpretty.activate
    def test_sync(self):
        """ Test create projects.json without URI. """

        api_page_1 = [
            {
                "id": 1,
                "name": "project_1",
                "full_name": "zhquan_example/project_1",
                "html_url": "https://github.com/zhquan_example/project_1",
                "clone_url": "https://github.com/zhquan_example/project_1.git",
                "fork": False
            },
            {
                "id": 2,
                "name": "project_2",
                "full_name": "zhquan_example/project_2",
                "html_url": "https://github.com/zhquan_example/project_2",
                "clone_url": "https://github.com/zhquan_example/project_2.git",
                "fork": False
            },
            {
                "id": 3,
                "name": "Project_3",
                "full_name": "zhquan_example/project_3",
                "html_url": "https://github.com/zhquan_example/project_3",
                "clone_url": "https://github.com/zhquan_example/project_3.git",
                "fork": False
            }
        ]

        httpretty.register_uri(httpretty.GET,
                               GITHUB_API_URL+"?page=1",
                               body=json.dumps(api_page_1),
                               status=200,
                               forcing_headers={
                                    'Link': '<' + GITHUB_API_URL + '/?&page=1>; rel="next", <' +
                                       GITHUB_API_URL + '/?&page=1>; rel="last"'
                               })

        blacklist = ["project_3"]
        github = GitHubSync(TOKEN)
        projects = {}
        projects = github.sync(projects, "zhquan_example", blacklist=blacklist)

        json_expected = {
            "zhquan_example": {
                "git": [
                    "https://github.com/zhquan_example/project_1.git",
                    "https://github.com/zhquan_example/project_2.git"
                ],
                "github": [
                    "https://github.com/zhquan_example/project_1",
                    "https://github.com/zhquan_example/project_2"
                ],
                "meta": {
                    "title": "zhquan_example"
                }
            }
        }

        self.assertDictEqual(json_expected, projects)

        expected = {
            'page': ['1']
        }
        self.assertDictEqual(httpretty.last_request().querystring, expected)

    @httpretty.activate
    def test_update_json(self):
        """ Test update the JSON file with the new repositories. """

        json_uri = {
            "zhquan_example": {
                "github": [
                    "https://github.com/zhquan_example/project_1",
                    "https://github.com/zhquan_example/project_2",
                    "https://github.com/zhquan_example/project_3",
                    "https://github.com/zhquan_example/project_4"
                ],
                "meta": {
                    "title": "zhquan_example"
                }
            }
        }
        httpretty.register_uri(httpretty.GET,
                               GITHUB_API_URL+"?page=1",
                               body=json.dumps(json_uri),
                               status=200)
        httpretty.register_uri(httpretty.GET,
                               URI,
                               body=json.dumps(json_uri),
                               status=200)
        httpretty.register_uri(httpretty.GET,
                               GITHUB_URL+"zhquan_example/project_1",
                               body="",
                               status=200)
        httpretty.register_uri(httpretty.GET,
                               GITHUB_URL+"zhquan_example/project_2",
                               body="",
                               status=404)
        httpretty.register_uri(httpretty.GET,
                               GITHUB_URL+"zhquan_example/project_3",
                               body="",
                               status=200)
        httpretty.register_uri(httpretty.GET,
                               GITHUB_URL+"zhquan_example/project_4",
                               body="",
                               status=404)

        github = GitHubSync(TOKEN)
        projects = github.load_projects(URI)
        github_list = ["https://github.com/zhquan_example/project_5", "https://github.com/zhquan_example/project_6"]
        projects = github.update_json("zhquan_example", projects, "github", github_list)

        json_expected = {
            "zhquan_example": {
                "github": [
                    "https://github.com/zhquan_example/project_1",
                    "https://github.com/zhquan_example/project_3",
                    "https://github.com/zhquan_example/project_5",
                    "https://github.com/zhquan_example/project_6"
                ],
                "meta": {
                    "title": "zhquan_example"
                }
            }
        }
        self.assertDictEqual(json_expected, projects)

    @httpretty.activate
    def test_get_repo(self):
        """ Test get all html_url and clone_url from a github project. """

        json_api = [
            {
                "id": 1,
                "name": "project_1",
                "full_name": "zhquan_example/project_1",
                "html_url": "https://github.com/zhquan_example/project_1",
                "clone_url": "https://github.com/zhquan_example/project_1.git",
                "fork": False
            },
            {
                "id": 2,
                "name": "project_2",
                "full_name": "zhquan_example/project_2",
                "html_url": "https://github.com/zhquan_example/project_2",
                "clone_url": "https://github.com/zhquan_example/project_2.git",
                "fork": False
            },
            {
                "id": 3,
                "name": "project_3",
                "full_name": "zhquan_example/project_3",
                "html_url": "https://github.com/zhquan_example/project_3",
                "clone_url": "https://github.com/zhquan_example/project_3.git",
                "fork": True
            }
        ]
        httpretty.register_uri(httpretty.GET,
                               GITHUB_API_URL+"?page=1",
                               body=json.dumps(json_api),
                               status=200,
                               forcing_headers={
                                    'Link': '<' + GITHUB_API_URL + '/?&page=1>; rel="next", <' +
                                       GITHUB_API_URL + '/?&page=1>; rel="last"'
                               })

        github = GitHubSync(TOKEN)
        git, github = github.get_repo("zhquan_example", False, [])

        git_expected = ['https://github.com/zhquan_example/project_1.git', 'https://github.com/zhquan_example/project_2.git']
        github_expected = ['https://github.com/zhquan_example/project_1', 'https://github.com/zhquan_example/project_2']
        self.assertListEqual(git_expected, git)
        self.assertListEqual(github_expected, github)

        github_fork = GitHubSync(TOKEN)
        git_fork, github_fork = github_fork.get_repo("zhquan_example", True, [])

        git_fork_expected = ['https://github.com/zhquan_example/project_1.git', 'https://github.com/zhquan_example/project_2.git', 'https://github.com/zhquan_example/project_3.git']
        github_fork_expected = ['https://github.com/zhquan_example/project_1', 'https://github.com/zhquan_example/project_2', 'https://github.com/zhquan_example/project_3']
        self.assertListEqual(git_fork_expected, git_fork)
        self.assertListEqual(github_fork_expected, github_fork)

    @httpretty.activate
    def test_get_url(self):
        """ Test get the github URL from github URI. """

        httpretty.register_uri(httpretty.GET,
                               URI,
                               body="",
                               status=200)
        httpretty.register_uri(httpretty.GET,
                               URI+"?token="+TOKEN,
                               body="",
                               status=200)

        github = GitHubSync(TOKEN)
        url = github.get_url(URI)
        url_expected = "https://zhquan_example:"+TOKEN+"@github.com/zhquan_example/project.git"
        self.assertEqual(url_expected, url)

        github_without_token = GitHubSync("")
        url_without_token = github_without_token.get_url(URI+"?token="+TOKEN)
        url_without_token_expected = "https://zhquan_example:"+TOKEN+"@github.com/zhquan_example/project.git"
        self.assertEqual(url_without_token_expected, url_without_token)

if __name__ == "__main__":
    unittest.main(warnings='ignore')
