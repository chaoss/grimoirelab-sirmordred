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
#     Luis Cañas-Díaz <lcanas@bitergia.com>
#

import logging
import urllib.request

from sirmordred.error import GithubFileNotFound

logger = logging.getLogger(__name__)


class Github:

    def __init__(self, token):
        self.token = token

    def __check_looks_like_uri(self, uri):
        """Checks the URI looks like a RAW uri in github:

        - 'https://raw.githubusercontent.com/github/hubot/master/README.md'
        - 'https://github.com/github/hubot/raw/master/README.md'

        :param uri: uri of the file
        """
        if uri.split('/')[2] == 'raw.githubusercontent.com':
            return True
        elif uri.split('/')[2] == 'github.com':
            if uri.split('/')[5] == 'raw':
                return True
        else:
            raise GithubFileNotFound('URI %s is not a valid link to a raw file in Github' % uri)

    def read_file_from_uri(self, uri):
        """Reads the file from Github

        :param uri: URI of the Github raw File

        :returns: UTF-8 text with the content
        """
        logger.debug("Reading %s" % (uri))

        self.__check_looks_like_uri(uri)

        try:
            req = urllib.request.Request(uri)
            req.add_header('Authorization', 'token %s' % self.token)
            r = urllib.request.urlopen(req)
        except urllib.error.HTTPError as err:
            if err.code == 404:
                raise GithubFileNotFound('File %s is not available. Check the URL to ensure it really exists' % uri)
            else:
                raise

        return r.read().decode("utf-8")
