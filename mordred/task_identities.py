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
import subprocess

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

    def __init__(self, config, load_ids=True):
        super().__init__(config)

        self.load_ids = load_ids  # Load identities from raw index
        self.sh_kwargs={'user': self.db_user, 'password': self.db_password,
                        'database': self.db_sh, 'host': self.db_host,
                        'port': None}

    def execute(self):

        #FIXME this should be called just once
        # code = 0 when command success
        code = Init(**self.sh_kwargs).run(self.db_sh)

        if not self.backend_section:
            logger.error("Backend not configured in TaskIdentitiesCollection %s", self.backend_section)
            return

        backend_conf = self.config.get_conf()[self.backend_section]

        if 'collect' in backend_conf and not backend_conf['collect']:
            logger.info("Don't load ids from a backend without collection %s", self.backend_section)
            return

        if self.load_ids:
            logger.info("[%s] Gathering identities from raw data", self.backend_section)
            enrich_backend = self._get_enrich_backend()
            ocean_backend = self._get_ocean_backend(enrich_backend)
            load_identities(ocean_backend, enrich_backend)
            #FIXME get the number of ids gathered


class TaskIdentitiesInit(Task):
    """ Basic class shared by all Sorting Hat tasks """

    def __init__(self, config):
        super().__init__(config)

        self.load_orgs = self.conf['sortinghat']['load_orgs']  # Load orgs from file
        self.sh_kwargs = {'user': self.db_user, 'password': self.db_password,
                          'database': self.db_sh, 'host': self.db_host,
                          'port': None}

    def is_backend_task(self):
        return False

    def execute(self):

        cfg = self.config.get_conf()

        # code = 0 when command success
        code = Init(**self.sh_kwargs).run(self.db_sh)

        if self.load_orgs:
            logger.info("[sortinghat] Loading orgs from file %s", cfg['sortinghat']['orgs_file'])
            code = Load(**self.sh_kwargs).run("--orgs", cfg['sortinghat']['orgs_file'])
            if code != CMD_SUCCESS:
                logger.error("[sortinghat] Error loading %s", cfg['sortinghat']['orgs_file'])
            #FIXME get the number of loaded orgs

        if 'identities_file' in cfg['sortinghat']:
            filenames = cfg['sortinghat']['identities_file']
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

    def __get_sh_command(self):
        cfg = self.config.get_conf()

        db_user = cfg['sortinghat']['user']
        db_password = cfg['sortinghat']['password']
        db_host = cfg['sortinghat']['host']
        db_name = cfg['sortinghat']['database']
        cmd = ['sortinghat', '-u', db_user, '-p', db_password, '--host', db_host,
               '-d', db_name]

        return cmd

    def do_affiliate(self):
        cmd = self.__get_sh_command()
        cmd += ['affiliate']
        logger.debug("Executing %s", cmd)
        return subprocess.call(cmd)
        # return Affiliate(**self.sh_kwargs).affiliate()

    def do_autoprofile(self, sources):
        cmd = self.__get_sh_command()
        cmd += ['autoprofile'] + sources
        logger.debug("Executing %s", cmd)
        return subprocess.call(cmd)
        # return  AutoProfile(**self.sh_kwargs).autocomplete(sources)


    def do_unify(self, kwargs):
        cmd = self.__get_sh_command()
        cmd += ['unify', '--fast-matching', '-m', kwargs['matching']]
        logger.debug("Executing %s", cmd)
        return subprocess.call(cmd)
        # return Unify(**self.sh_kwargs).unify(**kwargs)

    def execute(self):
        cfg = self.config.get_conf()

        if self.unify:
            for algo in cfg['sortinghat']['matching']:
                kwargs = {'matching':algo, 'fast_matching':True}
                logger.info("[sortinghat] Unifying identities using algorithm %s",
                            kwargs['matching'])
                # code = self.do_unify(kwargs)
                # if code != CMD_SUCCESS:
                #     logger.error("[sortinghat] Error in unify %s", kwargs)
                # Using subprocess approach to be sure memory is freed
                code = self.do_unify(kwargs)
                if code != 0:
                    logger.error("[sortinghat] Error in unify %s", kwargs)

        if self.affiliate:
            # Global enrollments using domains
            logger.info("[sortinghat] Executing affiliate")
            # code = self.do_affiliate()
            # if code != CMD_SUCCESS:
            #     logger.error("[sortinghat] Error in affiliate %s", kwargs)
            # Using subprocess approach to be sure memory is freed
            code = self.do_affiliate()
            if code != 0:
                logger.error("[sortinghat] Error in affiliate")

        if self.autoprofile:
            if not 'autoprofile' in cfg['sortinghat']:
                logger.info("[sortinghat] Autoprofile not configured. Skipping.")
            else:
                logger.info("[sortinghat] Executing autoprofile for sources: %s",
                            cfg['sortinghat']['autoprofile'])
                sources = cfg['sortinghat']['autoprofile']
                # code = self.do_autoprofile()
                # if code != CMD_SUCCESS:
                #     logger.error("Error in autoprofile %s", kwargs)
                # Using subprocess approach to be sure memory is freed
                code = self.do_autoprofile(sources)
                if code != 0:
                    logger.error("[sortinghat] Error in autoprofile %s", sources)

        if self.bots:
            if not 'bots_names' in cfg['sortinghat']:
                logger.info("[sortinghat] Bots name list not configured. Skipping.")
            else:
                logger.info("[sortinghat] Marking bots: %s",
                            cfg['sortinghat']['bots_names'])
                for name in cfg['sortinghat']['bots_names']:
                    # First we need the uuids for the profile name
                    uuids = self.__get_uuids_from_profile_name(name)
                    # Then we can modify the profile setting bot flag
                    profile = {"is_bot": True}
                    for uuid in uuids:
                        api.edit_profile(self.db, uuid, **profile)
                # For quitting the bot flag - debug feature
                if 'no_bots_names' in cfg['sortinghat']:
                    logger.info("[sortinghat] Removing Marking bots: %s",
                                cfg['sortinghat']['no_bots_names'])
                    for name in cfg['sortinghat']['no_bots_names']:
                        uuids = self.__get_uuids_from_profile_name(name)
                        profile = {"is_bot": False}
                        for uuid in uuids:
                            api.edit_profile(self.db, uuid, **profile)
