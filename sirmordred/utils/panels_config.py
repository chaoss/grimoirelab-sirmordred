#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2020 Bitergia
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
#     Valerio Cosentino <valcos@bitergia.com>
#

import argparse
import os
import sys

import panels
from sirmordred.config import Config
from sirmordred.task_panels import TaskPanels, TaskPanelsMenu


def get_params_parser():
    """Parse command line arguments"""

    parser = argparse.ArgumentParser(add_help=False)

    parser.add_argument('-g', '--debug', dest='debug',
                        action='store_true',
                        help=argparse.SUPPRESS)

    parser.add_argument("--cfg", dest='cfg_path',
                        help="Configuration file path")
    parser.add_argument("--dashboards", action='store_true', dest='dashboards',
                        help="Upload dashboards")
    parser.add_argument("--menu", action='store_true', dest='menu',
                        help="Upload menu")

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    return parser


def get_params():
    """Get params to upload dashboards and menu"""

    parser = get_params_parser()
    args = parser.parse_args()

    return args


def get_sigils_path():
    sigils_path = panels.__file__.replace('panels/__init__.py', '')
    return sigils_path


def read_file(filename, mode='r'):
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), filename), mode) as f:
        content = f.read()
    return content


def main():
    """This script allows to upload the dashboards in use in the setup.cfg and the top menu. It
    relies on the TaskPanels and TaskPanelsMenu classes.

    Examples:
        Upload dashboards and menu: panels_config --cfg ./setup.cfg --dashboards --menu
        Upload only the dashboards: panels_config --cfg ./setup.cfg --dashboards
        Upload only the top menu:   panels_config --cfg ./setup.cfg --menu
    """
    args = get_params()
    config = Config(args.cfg_path)

    upload_dashboards = args.dashboards
    upload_menu = args.menu

    if upload_dashboards:
        task = TaskPanels(config)
        task.execute()

    if upload_menu:
        task = TaskPanelsMenu(config)
        task.execute()


if __name__ == '__main__':
    main()
