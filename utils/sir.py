#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
#   Valerio Cosentino <valcos@bitergia.com>
#

import argparse
import logging
import sys

from sirmordred.config import Config
from sirmordred.sirmordred import SirMordred


def sir_mordred(cfg_path):
    """Execute sir mordred with the configuration file.

    :param cfg_path: the path of a Mordred configuration file
    """
    config = Config(cfg_path)
    sir = SirMordred(config)
    sir.start()


def config_logging(debug):
    """Config logging level output output"""

    if debug:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')
        logging.debug("Debug mode activated")
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')


def get_params_parser():
    """Parse command line arguments"""

    parser = argparse.ArgumentParser(add_help=False)

    parser.add_argument('-g', '--debug', dest='debug',
                        action='store_true',
                        help=argparse.SUPPRESS)

    parser.add_argument("--cfg", dest='cfg_path',
                        help="Configuration file path")

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    return parser


def get_params():
    """Get params to execute the mordred"""

    parser = get_params_parser()
    args = parser.parse_args()

    return args


if __name__ == '__main__':

    args = get_params()
    config_logging(args.debug)

    sir_mordred(args.cfg_path)
