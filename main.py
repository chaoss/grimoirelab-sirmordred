#!/usr/bin/env python3

# FIXME include GPL3 license here + authors

import sys
import time
import argparse
import logging

from datetime import datetime
from mordred import Mordred


##
log_file = "/tmp/mordred.log"
error_file = "/tmp/mordred.err"
stdout_file = log_file
stderr_file = log_file

def parse_args():

    parser = argparse.ArgumentParser(
        description='Daemon runner',
        epilog="That's all folks"
    )
    parser.add_argument('operation',
                    help='Accepts any of these values: start, stop, restart, '+\
                    'status',
                    choices=['start', 'stop', 'restart', 'status'])

    args = parser.parse_args()
    return args

### TO DO ###
# rewrite
def main():

    options = parse_args()
    # Daemon
    daemon = Mordred('/tmp/mordred.pid',stdout=stdout_file,stderr=stderr_file)

    if options.operation == 'start':
        print("Starting daemon")
        daemon.start()
        pid = daemon.get_pid()

        if not pid:
            print("Unable run daemon")
        else:
            print("Daemon is running [PID=%d]" % pid)

    elif options.operation == 'stop':
        print("Stoping daemon")
        daemon.stop()

    elif options.operation == 'restart':
        print("Restarting daemon")
        daemon.restart()
    elif options.operation == 'status':
        print("Viewing daemon status")
        pid = daemon.get_pid()

        if not pid:
            print("Daemon isn't running ;)")
        else:
            print("Daemon is running [PID=%d]" % pid)

    sys.exit(0)

if __name__ == '__main__':
    # https://docs.python.org/3/howto/logging.html
    logging.basicConfig(filename='/tmp/mordred.log',level=logging.DEBUG)
    main()
