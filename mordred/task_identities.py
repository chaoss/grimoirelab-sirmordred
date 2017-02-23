#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Bitergia
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
#     Luis Cañas-Díaz <lcanas@bitergia.com>
#     Alvaro del Castillo <acs@bitergia.com>
#

import logging

from mordred.task import Task
from sortinghat import api
from sortinghat.cmd.affiliate import Affiliate
from sortinghat.cmd.autoprofile import AutoProfile
from sortinghat.cmd.init import Init
from sortinghat.cmd.load import Load
from sortinghat.cmd.unify import Unify
from sortinghat.command import CMD_SUCCESS
from sortinghat.db.database import Database
from sortinghat.db.model import Profile

from grimoire_elk.arthur import load_identities

logger = logging.getLogger(__name__)


class TaskIdentitiesCollection(Task):
    """ Class aimed to get identites from raw data """

    def __init__(self, conf, load_ids=True):
        super().__init__(conf)

        #self.load_orgs = self.conf['sh_load_orgs']  # Load orgs from file
        self.load_ids = load_ids  # Load identities from raw index
        #self.unify = unify  # Unify identities
        #self.autoprofile = autoprofile  # Execute autoprofile
        #self.affiliate = affiliate # Affiliate identities
        self.sh_kwargs={'user': self.db_user, 'password': self.db_password,
                        'database': self.db_sh, 'host': self.db_host,
                        'port': None}

    def run(self):

        #FIXME this should be called just once
        # code = 0 when command success
        code = Init(**self.sh_kwargs).run(self.db_sh)

        if not self.backend_section:
            logger.error ("Backend not configured in TaskIdentitiesCollection.")
            return

        if self.load_ids:
            logger.info("[%s] Gathering identities from raw data" % self.backend_section)
            enrich_backend = self._get_enrich_backend()
            ocean_backend = self._get_ocean_backend(enrich_backend)
            load_identities(ocean_backend, enrich_backend)
            #FIXME get the number of ids gathered


class TaskIdentitiesInit(Task):
    """ Basic class shared by all Sorting Hat tasks """

    def __init__(self, conf):
        super().__init__(conf)

        self.load_orgs = self.conf['sh_load_orgs']  # Load orgs from file
        self.sh_kwargs={'user': self.db_user, 'password': self.db_password,
                        'database': self.db_sh, 'host': self.db_host,
                        'port': None}

    def is_backend_task(self):
        return False

    def run(self):

        # code = 0 when command success
        code = Init(**self.sh_kwargs).run(self.db_sh)

        if self.load_orgs:
            logger.info("[sortinghat] Loading orgs from file %s", self.conf['sh_orgs_file'])
            code = Load(**self.sh_kwargs).run("--orgs", self.conf['sh_orgs_file'])
            if code != CMD_SUCCESS:
                logger.error("[sortinghat] Error loading %s", self.conf['sh_orgs_file'])
            #FIXME get the number of loaded orgs

        if 'sh_ids_file' in self.conf.keys():
            filenames = self.conf['sh_ids_file'].split(',')
            for f in filenames:
                logger.info("[sortinghat] Loading identities from file %s", f)
                f = f.replace(' ','')
                code = Load(**self.sh_kwargs).run("--identities", f )
                if code != CMD_SUCCESS:
                    logger.error("[sortinghat] Error loading %s", f)


class TaskIdentitiesMerge(Task):
    """ Basic class shared by all Sorting Hat tasks """

    def __init__(self, conf, load_orgs=True, load_ids=True, unify=True,
                 autoprofile=True, affiliate=True, bots=True):
        super().__init__(conf)

        self.load_ids = load_ids  # Load identities from raw index
        self.unify = unify  # Unify identities
        self.autoprofile = autoprofile  # Execute autoprofile
        self.affiliate = affiliate # Affiliate identities
        self.bots = bots # Mark bots in SH
        self.sh_kwargs={'user': self.db_user, 'password': self.db_password,
                        'database': self.db_sh, 'host': self.db_host,
                        'port': None}
        self.db = Database(**self.sh_kwargs)

    def is_backend_task(self):
        return False

    def __get_uuids_from_profile_name(self, profile_name):
        """ Get the uuid for a profile name """
        uuids = []

        with self.db.connect() as session:
            query = session.query(Profile).\
            filter(Profile.name == profile_name)
            profiles = query.all()
            if profiles:
                for p in profiles:
                    uuids.append(p.uuid)
        return uuids

    def run(self):
        if self.unify:
            for algo in self.conf['sh_matching']:
                kwargs = {'matching':algo, 'fast_matching':True}
                logger.info("[sortinghat] Unifying identities using algorithm %s", kwargs['matching'])
                code = Unify(**self.sh_kwargs).unify(**kwargs)
                if code != CMD_SUCCESS:
                    logger.error("[sortinghat] Error in unify %s", kwargs)

        if self.affiliate:
            # Global enrollments using domains
            logger.info("[sortinghat] Executing affiliate")
            code = Affiliate(**self.sh_kwargs).affiliate()
            if code != CMD_SUCCESS:
                logger.error("[sortinghat] Error in affiliate %s", kwargs)


        if self.autoprofile:
            if not 'sh_autoprofile' in self.conf:
                logger.info("[sortinghat] Autoprofile not configured. Skipping.")
            else:
                logger.info("[sortinghat] Executing autoprofile: %s", self.conf['sh_autoprofile'])
                sources = self.conf['sh_autoprofile']
                code = AutoProfile(**self.sh_kwargs).autocomplete(sources)
                if code != CMD_SUCCESS:
                    logger.error("Error in autoprofile %s", kwargs)

        if self.bots:
            if not 'sh_bots_names' in self.conf:
                logger.info("[sortinghat] Bots name list not configured. Skipping.")
            else:
                logger.info("[sortinghat] Marking bots: %s",
                            self.conf['sh_bots_names'])
                for name in self.conf['sh_bots_names']:
                    # First we need the uuids for the profile name
                    uuids = self.__get_uuids_from_profile_name(name)
                    # Then we can modify the profile setting bot flag
                    profile = {"is_bot": True}
                    for uuid in uuids:
                        api.edit_profile(self.db, uuid, **profile)
                # For quitting the bot flag - debug feature
                if 'sh_no_bots_names' in self.conf:
                    logger.info("[sortinghat] Removing Marking bots: %s",
                                self.conf['sh_no_bots_names'])
                    for name in self.conf['sh_no_bots_names']:
                        uuids = self.__get_uuids_from_profile_name(name)
                        profile = {"is_bot": False}
                        for uuid in uuids:
                            api.edit_profile(self.db, uuid, **profile)
