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


class DataCollectionError(Exception):
    """Exception raise for error calling feed_backend method
    """
    def __init__(self, expression):
        self.expression = expression


class ElasticSearchError(Exception):
    """Exception raised for errors in the list of backends
    """
    def __init__(self, expression):
        self.expression = expression


class DataEnrichmentError(Exception):
    """Exception raised for error calling the enrich_backend method
    """
    def __init__(self, expression):
        self.expression = expression


class ConfigError(Exception):
    """Exception raised for errors in the configuration file.

    Attributes:
        expression -- input expression in which the error occurred
        message -- explanation of the error
    """
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message


class GithubFileNotFound(Exception):
    """Exception raised when getting a 404 from github
    """
    def __init__(self, message):
        self.message = message
