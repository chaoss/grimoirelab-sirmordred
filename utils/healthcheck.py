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


import argparse
import json
import re
import sys

from datetime import datetime
from file_read_backwards import FileReadBackwards
from sirmordred.config import Config

HEALTHCHECK_CACHEFILE = '/tmp/.mordred_healthcheck'
HEALTHCHECK_DATEFORMAT = '%Y-%m-%d %H:%M:%S,%f'
HEALTHCHECK_DESCRIPTION = "Healthcheck for SirMordred"
HEALTHCHECK_EPILOG = "Software metrics for your peace of mind"
HEALTHCHECK_LOGREGEXP = '[2][0-9]{3}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}.*'


def main():
    logs_dir, match_string = parse_args()
    time_b = datetime.now()
    healthy, time_a = read_cache_file()
    error_found = False

    if healthy and (time_a is not None):
        # We discard to search if the cache file is not created, this way the container
        #  won't have to worry about old logs
        file_path = logs_dir + '/all.log'
        error_found = match_error_string(file_path, time_a, time_b, match_string)
        healthy = not error_found

    write_cache_file(healthy, time_b)

    if not healthy:
        sys.exit(1)


def parse_args():
    """ Parses arguments and returns a tuple with the path of the logs dir and the string to be found """

    parser = argparse.ArgumentParser(
        description=HEALTHCHECK_DESCRIPTION,
        epilog=HEALTHCHECK_EPILOG
    )

    parser.add_argument('-c', '--config', help='Configuration file',
                        type=str, default=['setup.cfg'],
                        dest='config_file')
    parser.add_argument('-s', '--string', help='String to match errors in log file',
                        type=str,
                        dest='match_string')

    args = parser.parse_args()

    config = Config(args.config_file)
    config_dict = config.get_conf()

    return config_dict['general']['logs_dir'], args.match_string


def read_cache_file():
    """Reads the content of the cache file with the data of the last execution.

    :returns: tuple with boolean and a datetime if file is found. True, None if any exception is raised
    """
    default_output = True, None
    try:
        with open(HEALTHCHECK_CACHEFILE, 'r') as f:
            cache = json.load(f)
            return cache['healthy'], datetime.strptime(cache['time'], HEALTHCHECK_DATEFORMAT)

    except FileNotFoundError:
        return default_output
    except json.decoder.JSONDecodeError:
        return default_output
    except KeyError:
        return default_output


def match_error_string(file_path, time_a, time_b, match_string):
    """Searches a string in a log file for all the lines where date is between time_a and time_b

    :param logs_dir: path of the directory where log file is located
    :param time_a: time which defines the starting point of the time frame
    :param time_b: time which defines the ending point of the time frame
    :param match_string: string to be search in any log lines
    :returns: If the string is found it returns True. False is returned otherwise
    """
    with FileReadBackwards(file_path, encoding="utf-8") as frb:
        for line in frb:
            match = re.match(HEALTHCHECK_LOGREGEXP, line)
            if not match:
                continue

            columns = line.split(' ')
            str_date = columns[0] + ' ' + columns[1]
            dt_line = datetime.strptime(str_date, HEALTHCHECK_DATEFORMAT)
            if dt_line < time_a or dt_line > time_b:
                break

            if line.find(match_string) > 0:
                return True

    return False


def write_cache_file(is_healthy, time):
    """Stores a JSON with a boolean and a datetime timestamp in the cache file

    :param is_healthy: boolean
    :param time: datetime
    """

    cache_content = {}
    cache_content['time'] = time.strftime(HEALTHCHECK_DATEFORMAT)
    cache_content['healthy'] = is_healthy

    with open(HEALTHCHECK_CACHEFILE, 'w+') as f:
        f.write(json.dumps(cache_content))


if __name__ == '__main__':
    main()
