#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2021 Bitergia
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
#     Quan Zhou <quan@bitergia.com>
#

import logging
import time

from datetime import datetime

from grimoire_elk.enriched.sortinghat_gelk import SortingHat

from sirmordred.task import Task
from sirmordred.task_manager import TasksManager

logger = logging.getLogger(__name__)


class TaskIdentitiesMerge(Task):
    """ Task for processing identities in SortingHat """

    def __init__(self, conf, sortinghat_client):
        super().__init__(conf, sortinghat_client)
        self.last_autorefresh = datetime.utcnow()  # Last autorefresh date

    def is_backend_task(self):
        return False

    def execute(self):

        # ** START SYNC LOGIC **
        # Check that enrichment tasks are not active before loading identities
        while True:
            time.sleep(1)  # check each second if the task could start
            with TasksManager.IDENTITIES_TASKS_ON_LOCK:
                with TasksManager.NUMBER_ENRICH_TASKS_ON_LOCK:
                    enrich_tasks = TasksManager.NUMBER_ENRICH_TASKS_ON
                    logger.debug("[unify] Enrich tasks active: %i", enrich_tasks)
                    if enrich_tasks == 0:
                        # The load of identities can be started
                        TasksManager.IDENTITIES_TASKS_ON = True
                        break
        #  ** END SYNC LOGIC **

        cfg = self.config.get_conf()

        for algo in cfg['sortinghat']['matching']:
            if not algo:
                # cfg['sortinghat']['matching'] is an empty list
                logger.debug('Unify not executed because empty algorithm')
                continue
            kwargs = {'matching': algo, 'fast_matching': True,
                      'strict_mapping': cfg['sortinghat']['strict_mapping']}
            logger.info("[sortinghat] Unifying identities using algorithm %s",
                        kwargs['matching'])
            SortingHat.do_unify(self.client, kwargs)

        if not cfg['sortinghat']['affiliate']:
            logger.debug("Not doing affiliation")
        else:
            # Global enrollments using domains
            logger.info("[sortinghat] Executing affiliate")
            SortingHat.do_affiliate(self.client)

        if 'autogender' not in cfg['sortinghat'] or \
                not cfg['sortinghat']['autogender']:
            logger.info("[sortinghat] Autogender not configured. Skipping.")
        else:
            logger.info("[sortinghat] Executing autogender")
            SortingHat.do_autogender(self.client)

        with TasksManager.IDENTITIES_TASKS_ON_LOCK:
            TasksManager.IDENTITIES_TASKS_ON = False
