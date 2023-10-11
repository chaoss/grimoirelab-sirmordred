#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2023 Bitergia
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
#     Alvaro del Castillo <acs@bitergia.com>
#


import argparse
import logging
import logging.handlers
import os
import sys

sys.path.insert(1, '.')

# Quick fix for avoiding weird warnings
# https://github.com/chaoss/grimoirelab-sirmordred/issues/192
import warnings
warnings.filterwarnings("ignore", message="numpy.dtype size changed")
warnings.filterwarnings("ignore", message="numpy.ufunc size changed")

from sirmordred.config import Config
from sirmordred.sirmordred import SirMordred


SLEEPFOR_ERROR = """Error: You may be Arthur, King of the Britons. But you still """ + \
                 """need the 'sleep_for' variable in sortinghat section\n - Sir Mordred said."""

Logger = logging.getLogger(__name__)


def main():
    args = parse_args()

    if args.config_template_file is not None:
        Config.create_config_file(args.config_template_file)
        Logger.info("Sample config file created in {}".format(args.config_template_file))
        return 0
    elif args.config_files is None:
        Logger.error("Option -t or -c is required")
        return 1

    try:
        config = Config(args.config_files[0], args.config_files[1:])
        config_dict = config.get_conf()
        logs_dir = config_dict['general'].get('logs_dir', None)
        debug_mode = config_dict['general']['debug']
        short_name = config_dict['general']['short_name']
        logger = setup_logs(logs_dir, debug_mode, short_name)
    except RuntimeError as error:
        print("Error while consuming configuration: {}".format(error))
        return 1

    if args.phases:
        logger.info("Executing sirmordred for phases: {}".format(args.phases))
        # HACK: the internal dict of Config is modified directly
        # In manual phases execute sirmordred as an script
        config_dict['general']['update'] = False
        for phase in config_dict['phases']:
            config_dict['phases'][phase] = True if phase in args.phases else False

    SirMordred(config).start()


def setup_logs(logs_dir, debug_mode, short_name):

    if debug_mode:
        logging_mode = logging.DEBUG
    else:
        logging_mode = logging.INFO

    logger = logging.getLogger()
    logger.setLevel(logging_mode)

    # create formatter and add it to the handlers
    formatter = logging.Formatter(f'%(asctime)s - {short_name} - %(name)s - %(levelname)s - %(message)s')

    # create file handler
    if logs_dir:
        fh_filepath = os.path.join(logs_dir, 'all.log')
        fh = logging.FileHandler(fh_filepath)
        fh.setLevel(logging_mode)
        # Set format
        fh.setFormatter(formatter)
        # add the handlers to the logger
        logger.addHandler(fh)

    # create console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging_mode)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # this is needed because the perceval log messages are similar to ELK/mordred ones
    if not debug_mode:
        logging.getLogger('perceval').setLevel(logging.WARNING)

    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('urrlib3').setLevel(logging.WARNING)
    logging.getLogger('elasticsearch').setLevel(logging.WARNING)

    return logger


def parse_args():
    parser = argparse.ArgumentParser(
        description='SirMordred, the friendly friend of GrimoireELK',
        epilog='Software metrics for your peace of mind'
    )

    parser.add_argument('-c', '--config', help='Configuration files',
                        type=str, nargs='+', default=['mordred.cfg'],
                        dest='config_files')
    parser.add_argument('-t', '--template', help='Create template configuration file',
                        dest='config_template_file')
    parser.add_argument('-p', '--phases', nargs='*',
                        help='List of phases to execute (update is set to false)')

    args = parser.parse_args()
    return args


if __name__ == '__main__':
    try:
        code = main()
        sys.exit(code)
    except KeyboardInterrupt:
        s = "\n\nReceived Ctrl-C or other break signal. Exiting.\n"
        sys.stderr.write(s)
        sys.exit(0)
    except RuntimeError as e:
        s = "Error: %s\n" % str(e)
        sys.stderr.write(s)
        sys.exit(1)
