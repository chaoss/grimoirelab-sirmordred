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
#   Valerio Cosentino <valcos@bitergia.com>
#

import argparse
import logging
import os

import colorlog
import sys

from sirmordred.config import Config
from sirmordred.task_collection import TaskRawDataCollection
from sirmordred.task_identities import TaskIdentitiesMerge, TaskIdentitiesLoad
from sirmordred.task_enrich import TaskEnrich
from sirmordred.task_panels import TaskPanels, TaskPanelsMenu
from sirmordred.task_projects import TaskProjects

DEBUG_LOG_FORMAT = "[%(asctime)s - %(name)s - %(levelname)s] - %(message)s"
INFO_LOG_FORMAT = "%(asctime)s %(message)s"
COLOR_LOG_FORMAT_SUFFIX = "\033[1m %(log_color)s "
LOG_COLORS = {'DEBUG': 'white', 'INFO': 'cyan', 'WARNING': 'yellow', 'ERROR': 'red', 'CRITICAL': 'red,bg_white'}


def micro_mordred(cfg_path, backend_sections, raw, identities_load, identities_merge, enrich, panels):
    """Execute the Mordred tasks using the configuration file (`cfg_path`).

    :param cfg_path: the path of a Mordred configuration file
    :param backend_sections: the backend sections where the raw/enrich/identities phases will be executed
    :param raw: if true, it activates the collection of raw data
    :param identities_load: if true, it activates the identities loading process
    :param identities_merge: if true, it activates the identities merging process
    :param enrich: if true, it activates the enrichment of the raw data
    :param panels: if true, it activates the upload of all panels declared in the configuration file
    """

    config = Config(cfg_path)

    if raw:
        for backend in backend_sections:
            get_raw(config, backend)

    if identities_load:
        get_identities_load(config)

    if identities_merge:
        get_identities_merge(config)

    if enrich:
        for backend in backend_sections:
            get_enrich(config, backend)

    if panels:
        get_panels(config)


def get_raw(config, backend_section):
    """Execute the raw phase for a given backend section

    :param config: a Mordred config object
    :param backend_section: the backend section where the raw phase is executed
    """

    task = TaskRawDataCollection(config, backend_section=backend_section)
    TaskProjects(config).execute()
    try:
        task.execute()
        logging.info("Loading raw data finished!")
    except Exception as e:
        logging.error(str(e))
        sys.exit(-1)


def get_identities_merge(config):
    """Execute the merge identities phase

    :param config: a Mordred config object
    """
    TaskProjects(config).execute()
    task = TaskIdentitiesMerge(config)
    task.execute()
    logging.info("Merging identities finished!")


def get_identities_load(config):
    """Execute the load identities phase

    :param config: a Mordred config object
    """
    TaskProjects(config).execute()
    task = TaskIdentitiesLoad(config)
    task.execute()
    logging.info("Loading identities finished!")


def get_enrich(config, backend_section):
    """Execute the enrich phase for a given backend section

    :param config: a Mordred config object
    :param backend_section: the backend section where the enrich phase is executed
    """

    TaskProjects(config).execute()
    task = TaskEnrich(config, backend_section=backend_section)
    try:
        task.execute()
        logging.info("Loading enriched data finished!")
    except Exception as e:
        logging.error(str(e))
        sys.exit(-1)


def get_panels(config):
    """Execute the panels phase

    :param config: a Mordred config object
    """

    task = TaskPanels(config)
    task.execute()

    task = TaskPanelsMenu(config)
    task.execute()

    logging.info("Panels creation finished!")


def config_logging(debug, logs_dir):
    """Config logging level output output"""

    if debug:
        fmt = DEBUG_LOG_FORMAT
        logging_mode = logging.DEBUG
    else:
        fmt = INFO_LOG_FORMAT
        logging_mode = logging.INFO

    # Setting the color scheme and level into the root logger
    logging.basicConfig(level=logging_mode)
    stream = logging.root.handlers[0]
    formatter = colorlog.ColoredFormatter(fmt=COLOR_LOG_FORMAT_SUFFIX + fmt,
                                          log_colors=LOG_COLORS)
    stream.setFormatter(formatter)

    # Creating a file handler and adding it to root
    if logs_dir:
        fh_filepath = os.path.join(logs_dir, 'all.log')
        fh = logging.FileHandler(fh_filepath, mode='w')
        fh.setLevel(logging_mode)
        formatter = logging.Formatter(fmt)
        fh.setFormatter(formatter)
        logging.getLogger().addHandler(fh)

    # ES logger is set to INFO since, it produces a really verbose output if set to DEBUG
    logging.getLogger('elasticsearch').setLevel(logging.INFO)

    # Show if debug mode is activated
    if debug:
        logging.debug("Debug mode activated")


def get_params_parser():
    """Parse command line arguments"""

    parser = argparse.ArgumentParser(add_help=False)

    parser.add_argument('-g', '--debug', dest='debug',
                        action='store_true',
                        help=argparse.SUPPRESS)
    parser.add_argument("--raw", action='store_true', dest='raw',
                        help="Activate raw task")
    parser.add_argument("--enrich", action='store_true', dest='enrich',
                        help="Activate enrich task")
    parser.add_argument("--identities-load", action='store_true', dest='identities_load',
                        help="Activate load identities task")
    parser.add_argument("--identities-merge", action='store_true', dest='identities_merge',
                        help="Activate merge identities task")
    parser.add_argument("--panels", action='store_true', dest='panels',
                        help="Activate panels task")

    parser.add_argument("--cfg", dest='cfg_path',
                        help="Configuration file path")
    parser.add_argument("--backends", dest='backend_sections', default=[],
                        nargs='*', help="Backend sections to execute")
    parser.add_argument("--logs-dir", dest='logs_dir', default='', help='Logs Directory')

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    return parser


def get_params():
    """Get params to execute micro-mordred"""

    parser = get_params_parser()
    args = parser.parse_args()

    tasks = [args.raw, args.enrich, args.identities_load, args.identities_merge, args.panels]

    if not any(tasks):
        print("No tasks enabled")
        sys.exit(1)

    return args


if __name__ == '__main__':
    args = get_params()
    config_logging(args.debug, args.logs_dir)
    micro_mordred(args.cfg_path, args.backend_sections,
                  args.raw,
                  args.identities_load,
                  args.identities_merge,
                  args.enrich,
                  args.panels)
