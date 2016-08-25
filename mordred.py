#!/usr/bin/env python3

# FIXME include the UTF8 thing if needed with python3

# FIXME include GPL3 license here + authors

import configparser
import logging
import os
import subprocess
import time

from datetime import datetime
from pydaemon import Daemon
from redis import Redis
from rq import Connection, Worker, Queue



class Mordred(Daemon):

    # can I overwrite the init? I would like to store paths for conf files

    def read_conf_files(self):

        path = "/etc/mordred" #hardcoded

        confs = {}

        for entry in os.scandir(path):
            if not entry.name.startswith('.') and entry.is_file():
                logging.info(entry.name)
                #https://docs.python.org/3/library/configparser.html
                config = configparser.ConfigParser()
                config.read(os.path.join(path,entry.name))
                logging.info(config.sections())

                try:
                    if 'sleep' in config['general'].keys():
                        #if config['general'].has_key('sleep'):
                        sleep = config.get('general','sleep')
                    else:
                        sleep = 0
                    env_name = entry.name.replace('.conf','')
                    confs[env_name] = sleep
                except KeyError:
                    logging.error("'general' section is missing from %s " + \
                                "conf file", entry.name)

        return confs

    def _worker_is_running (self, name):
        # returns true if worker named with 'name' is running
        with Connection():
            current_workers = Worker.all()
        w_names = []

        for w in current_workers:
            w_names.append(w.name)

        return name in w_names

    def run(self):
        while True:

            confs = self.read_conf_files()

            for key, value in confs.items():
                logging.info("ENV %s, SLEEP %s" % (key,value))

                if not self._worker_is_running(key):
                    try:
                        args = ['/usr/local/bin/rq','worker', key, '--name', key]
                        subprocess.Popen(args)
                    except:
                        #FIXME handle the error
                        logging.error("Non handled exception calling to 'rq worker'")
                else:
                    logging.debug("Worker %s already exists" % key)

            ## existen cola x y tiene trabajo?
                ## si no: crear colas si no existen
                ##        encolar trabajos
            ## yes: pass

            time.sleep(10)
