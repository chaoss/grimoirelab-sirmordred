#!/usr/bin/env python3

import sys
import time
import argparse
import logging
import configparser

from datetime import datetime
from pydaemon import Daemon


class Mordred(Daemon):

    def run(self):
        config = configparser.ConfigParser()
        config.read('/path/test.cfg')
        logging.debug(config.get('config', 'myvar'))
        while True:
            time.sleep(0.1)
