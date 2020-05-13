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
#     Alvaro del Castillo <acs@bitergia.com>
#

import base64
import gzip
import hashlib
import json
import logging
import os
import shutil
import subprocess
import tempfile
import time

from datetime import datetime

import requests

from sirmordred.task import Task
from sirmordred.task_manager import TasksManager
from sortinghat.cmd.init import Init
from sortinghat.cmd.load import Load
from sortinghat.cmd.export import Export
from sortinghat.command import CMD_SUCCESS
from sortinghat.db.database import Database
from sortinghat.db.model import Profile

from grimoire_elk.elk import load_identities

logger = logging.getLogger(__name__)


def get_file_hash(filepath):
    """Generate hash based on the file content

    Read the content of a JSON file, remove all no alphanumeric
    characters, sort the remaining characters and create a hash from them.

    :param filepath: local path of the file to hash
    :return: content hash
    """
    with open(filepath, 'r') as f:
        content = f.read()

    json_content = json.loads(content)
    # Remove the attribute time for identities file, since its value changes
    # any time the file is generated
    json_content.pop('time', None)
    json_dump = json.dumps(json_content)

    digest_content = "".join([c if c.isalnum() else "" for c in sorted(json_dump)]).strip()
    hash_object = hashlib.sha256()
    hash_object.update(digest_content.encode('utf-8'))
    return hash_object.hexdigest()


class TaskInitSortingHat(Task):
    """ Class aimed to create the SH database """

    def __init__(self, config):
        super().__init__(config)

    def is_backend_task(self):
        return False

    def execute(self):
        code = Init(**self.sh_kwargs).run(self.db_sh, '--reuse')

        if code != 0:
            logger.warning("Can not create the SortingHat database")

        logger.debug("Sortinghat initialized")


class TaskIdentitiesCollection(Task):
    """ Class aimed to get identites from raw data """

    def __init__(self, config, load_ids=True):
        super().__init__(config)

        self.load_ids = load_ids  # Load identities from raw index

    def execute(self):

        # FIXME this should be called just once
        # code = 0 when command success
        code = Init(**self.sh_kwargs).run(self.db_sh, '--reuse')

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
            # FIXME get the number of ids gathered


class TaskIdentitiesLoad(Task):
    def __init__(self, config):
        super().__init__(config)

        self.current_orgs_file_hash = None
        self.current_identities_files_hash = {}

    def is_backend_task(self):
        return False

    def __execute_command(self, cmd):
        logger.debug("Executing %s", cmd)
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        outs, errs = proc.communicate()
        if proc.returncode != 0:
            logger.error("[sortinghat] Error in command %s", cmd)
        return proc.returncode

    def execute(self):

        def is_remote(filename):
            """ Naive implementation. To be evolved """
            remote = False
            if 'http' in filename:
                return True
            return remote

        def load_identities_file(filename, reset=False):
            """
            Load an identities file in Sortinghat with reset option

            The reset option cleans all merges and affiliations in identities that will be
            loaded to honor the identities grouping from the file.
            """
            if reset:
                logger.info("[sortinghat] Loading identities with reset from file %s", filename)
                code = Load(**self.sh_kwargs).run("--reset", "--identities", filename)
            else:
                content_hash = get_file_hash(filename)
                if content_hash not in self.current_identities_files_hash:
                    logger.info("[sortinghat] Loading identities from file %s", filename)
                    code = Load(**self.sh_kwargs).run("--identities", filename)
                    self.current_identities_files_hash.update({content_hash: {'filename': filename, 'has_changed': 1}})
                else:
                    self.current_identities_files_hash.update({content_hash: {'filename': filename, 'has_changed': 0}})
                    logger.info("[sortinghat] No changes in file %s, identities won't be loaded", filename)
                    code = CMD_SUCCESS

            if code != CMD_SUCCESS:
                logger.error("[sortinghat] Error loading %s", filename)
            logger.info("[sortinghat] End of loading identities from file %s", filename)

        def load_sortinghat_identities(config):
            """ Load identities from a file in SortingHat JSON format """

            cfg = config.get_conf()

            filenames = cfg['sortinghat']['identities_file']
            api_token = cfg['sortinghat']['identities_api_token']
            for filename in filenames:
                filename = filename.replace(' ', '')  # spaces used in config file list
                if filename == '':
                    continue
                if is_remote(filename):
                    # Use the GitHub Data API to get the file
                    # First we need the SHA for this file
                    try:
                        # https://github.com/<owner>/<repo>/blob/<branch>/<sh_identities>
                        repo_file = filename.rsplit("/", 1)[1]
                        repository_raw = filename.rsplit("/", 1)[0]
                        repository = repository_raw.rsplit("/", 2)[0]
                        repository_api = repository.replace('github.com', 'api.github.com/repos')
                        # repository_type = repository_raw.rsplit("/", 2)[1]
                        repository_branch = repository_raw.rsplit("/", 2)[2]
                        repo_file_sha = \
                            TaskIdentitiesExport.sha_github_file(config, repo_file,
                                                                 repository_api, repository_branch)
                        if not repo_file_sha:
                            logger.error("Can't find identities file %s. Not loading identities", filename)
                            return
                        file_url = repository_api + "/git/blobs/" + repo_file_sha
                        headers = {"Authorization": "token " + api_token}
                        res = requests.get(file_url, headers=headers)
                        res.raise_for_status()
                        with tempfile.NamedTemporaryFile() as temp:
                            temp.write(base64.b64decode(res.json()['content']))
                            temp.flush()
                            load_identities_file(temp.name, cfg['sortinghat']['reset_on_load'])
                    except IndexError as ex:
                        logger.error("Can not load identities from: %s", filename)
                        logger.debug("Expected format: https://github.com/owner/repo/blob/master/file")
                        logger.debug(ex)
                else:
                    load_identities_file(filename, cfg['sortinghat']['reset_on_load'])

        def load_grimoirelab_identities(config):
            """ Load identities from files in GrimoireLab YAML format """

            logger.info("Loading GrimoireLab identities in SortingHat")

            cfg = config.get_conf()

            # Get the identities
            identities_url = cfg['sortinghat']['identities_file'][0]

            if not is_remote(identities_url):
                identities_filename = identities_url
            else:
                # The file should be in gitlab in other case
                if 'identities_api_token' not in cfg['sortinghat']:
                    logger.error("API Token not provided. Identities won't be loaded")
                    return
                token = cfg['sortinghat']['identities_api_token']
                res = requests.get(identities_url, headers={"PRIVATE-TOKEN": token})
                res.raise_for_status()
                identities = tempfile.NamedTemporaryFile()
                identities.write(res.content)
                identities.flush()
                identities_filename = identities.name

            # Convert to a JSON file in SH format
            # grimoirelab2sh -i identities.yaml -s ssf:manual -o ssf.json
            json_identities = tempfile.mktemp()
            cmd = ['grimoirelab2sh', '-i', identities_filename,
                   '-s', cfg['general']['short_name'] + ':manual',
                   '-o', json_identities]
            if not cfg['sortinghat']['strict_mapping']:
                cmd += ['--no-email-validation']
                cmd += ['--no-enrollment-periods-validation']
            if self.__execute_command(cmd) != 0:
                logger.error('Can not generate the SH JSON file from '
                             'GrimoireLab yaml file. Do the files exists? '
                             'Is the API token right?')
            else:
                # Load the JSON file in SH format
                load_identities_file(json_identities, cfg['sortinghat']['reset_on_load'])

                # Closing tmp files so they are removed for the remote case
                if is_remote(identities_url):
                    identities.close()

                os.remove(json_identities)

        # ** START SYNC LOGIC **
        # Check that enrichment tasks are not active before loading identities
        while True:
            time.sleep(1)  # check each second if the identities load could start
            with TasksManager.IDENTITIES_TASKS_ON_LOCK:
                with TasksManager.NUMBER_ENRICH_TASKS_ON_LOCK:
                    enrich_tasks = TasksManager.NUMBER_ENRICH_TASKS_ON
                    logger.debug("[load identities] Enrich tasks active: %i", enrich_tasks)
                    if enrich_tasks == 0:
                        # The load of identities can be started
                        TasksManager.IDENTITIES_TASKS_ON = True
                        break
        #  ** END SYNC LOGIC **

        cfg = self.config.get_conf()

        # code = 0 when command success
        code = Init(**self.sh_kwargs).run(self.db_sh, '--reuse')

        # Basic loading of organizations from a SH JSON file. Legacy stuff.
        if 'load_orgs' in cfg['sortinghat'] and cfg['sortinghat']['load_orgs']:
            if 'orgs_file' not in cfg['sortinghat'] or not cfg['sortinghat']['orgs_file']:
                logger.error("Load orgs active but no orgs_file configured")
            elif not os.path.exists(cfg['sortinghat']['orgs_file']):
                logger.error("Orgs file not found on disk")
            else:
                orgs_file = cfg['sortinghat']['orgs_file']
                orgs_file_hash = get_file_hash(orgs_file)
                if not self.current_orgs_file_hash or self.current_orgs_file_hash != orgs_file_hash:
                    logger.info("[sortinghat] Loading orgs from file %s", orgs_file)
                    code = Load(**self.sh_kwargs).run("--orgs", orgs_file)
                    if code != CMD_SUCCESS:
                        logger.error("[sortinghat] Error loading %s", orgs_file)

                    self.current_orgs_file_hash = orgs_file_hash
                    with open(orgs_file, 'r') as f:
                        json_content = json.loads(f.read())
                    logger.info("[sortinghat] %s organizations loaded", len(json_content['organizations']))
                else:
                    logger.info("[sortinghat] No changes in file %s, organizations won't be loaded", orgs_file)

        # Identities loading from files. It could be in several formats.
        # Right now GrimoireLab and SortingHat formats are supported
        if 'identities_file' in cfg['sortinghat']:
            try:
                if cfg['sortinghat']['identities_format'] == 'sortinghat':
                    load_sortinghat_identities(self.config)
                elif cfg['sortinghat']['identities_format'] == 'grimoirelab':
                    load_grimoirelab_identities(self.config)
            except Exception:
                with TasksManager.IDENTITIES_TASKS_ON_LOCK:
                    TasksManager.IDENTITIES_TASKS_ON = False
                raise

            # we need to unify in order to mix the identities loaded with then ones
            # from data sources.
            cmd = ['sortinghat', '-u', self.db_user, '-p', self.db_password,
                   '--host', self.db_host, '-d', self.db_sh]
            cmd += ['unify', '--fast-matching']
            for algo in cfg['sortinghat']['matching']:
                ucmd = cmd + ['-m', algo]
                if not cfg['sortinghat']['strict_mapping']:
                    ucmd += ['--no-strict-matching']
                logger.debug("Doing unify after identities load")
                self.__execute_command(ucmd)

            if 'affiliate' in cfg['sortinghat'] and cfg['sortinghat']['affiliate']:
                cmd = ['sortinghat', '-u', self.db_user, '-p', self.db_password,
                       '--host', self.db_host, '-d', self.db_sh]
                cmd += ['affiliate']
                logger.debug("Doing affiliate after identities load")
                self.__execute_command(cmd)

        with TasksManager.IDENTITIES_TASKS_ON_LOCK:
            TasksManager.IDENTITIES_TASKS_ON = False


class TaskIdentitiesExport(Task):
    def __init__(self, config):
        super().__init__(config)

    def is_backend_task(self):
        return False

    @classmethod
    def sha_github_file(cls, config, repo_file, repository_api, repository_branch):
        """ Return the GitHub SHA for a file in the repository """

        repo_file_sha = None

        cfg = config.get_conf()
        github_token = cfg['sortinghat']['identities_api_token']
        headers = {"Authorization": "token " + github_token}

        url_dir = repository_api + "/git/trees/" + repository_branch
        logger.debug("Gettting sha data from tree: %s", url_dir)
        raw_repo_file_info = requests.get(url_dir, headers=headers)
        raw_repo_file_info.raise_for_status()
        for rfile in raw_repo_file_info.json()['tree']:
            if rfile['path'] == repo_file:
                logger.debug("SHA found: %s, ", rfile["sha"])
                repo_file_sha = rfile["sha"]
                break

        return repo_file_sha

    def execute(self):

        def export_identities(filename):
            """ Export Sortinghat identities to a file """
            logger.info("[sortinghat] Exporting identities to %s", filename)
            code = Export(**self.sh_kwargs).run("--identities", filename)
            if code != CMD_SUCCESS:
                logger.error("[sortinghat] Error exporting %s", filename)

        cfg = self.config.get_conf()

        if cfg['sortinghat']['identities_export_url'] is None:
            return

        if cfg['sortinghat']['identities_api_token'] is None:
            logger.error("identities_api_token for uploading data to GitHub not found in sortinghat section")
            return

        repo_file_sha = None
        gzipped_identities_file = None
        github_token = cfg['sortinghat']['identities_api_token']
        headers = {"Authorization": "token " + github_token}

        repository_url = cfg['sortinghat']['identities_export_url']
        try:
            # https://github.com/<owner>/<repo>/blob/<branch>/<sh_identities>.gz
            repo_file = repository_url.rsplit("/", 1)[1]
            repository_raw = repository_url.rsplit("/", 1)[0]
            repository = repository_raw.rsplit("/", 2)[0]
            repository_api = repository.replace('github.com', 'api.github.com/repos')
            # repository_type = repository_raw.rsplit("/", 2)[1]
            repository_branch = repository_raw.rsplit("/", 2)[2]
        except IndexError as ex:
            logger.error("Can not export identities to: %s", repository_url)
            logger.debug("Expected format: https://github.com/owner/repo/blob/master/file")
            logger.debug(ex)

            return

        with tempfile.NamedTemporaryFile() as temp:
            export_identities(temp.name)
            logger.debug("SH identities exported to tmp file: %s", temp.name)
            # Compress the file with gzip
            with open(temp.name, 'rb') as f_in:
                gzipped_identities_file = temp.name + '.gz'
                with gzip.open(gzipped_identities_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            # Get sha for the repository_file
            repo_file_sha = self.sha_github_file(self.config, repo_file,
                                                 repository_api, repository_branch)
            if repo_file_sha is None:
                logger.debug("Can not find sha for %s. It will be created.", repository_url)

            # Upload gzipped file to repository_file
            logger.debug("Encoding to base64 identities file")
            with open(gzipped_identities_file, "rb") as raw_file:
                base64_raw = base64.b64encode(raw_file.read())
                # base64 is ascii encoded data
                gzipped_base64_identities = base64_raw.decode('ascii')
                upload_json = {
                    "content": gzipped_base64_identities,
                    "message": "sirmordred automatic update"
                }
                if repo_file_sha:
                    upload_json["sha"] = repo_file_sha

                data = json.dumps(upload_json)
                url_put = repository_api + "/contents/" + repo_file
                logger.debug("Uploading to GitHub %s", url_put)
                upload_res = requests.put(url_put, headers=headers, data=data)
                upload_res.raise_for_status()


class TaskIdentitiesMerge(Task):
    """ Task for processing identities in SortingHat """

    def __init__(self, conf):
        super().__init__(conf)
        self.db = Database(**self.sh_kwargs)
        self.last_autorefresh = datetime.utcnow()  # Last autorefresh date

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

    def __build_sh_command(self):
        cfg = self.config.get_conf()

        db_user = cfg['sortinghat']['user']
        db_password = cfg['sortinghat']['password']
        db_host = cfg['sortinghat']['host']
        db_name = cfg['sortinghat']['database']
        cmd = ['sortinghat', '-u', db_user, '-p', db_password, '--host', db_host,
               '-d', db_name]

        return cmd

    def __execute_sh_command(self, cmd):
        logger.debug("Executing %s", cmd)
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        outs, errs = proc.communicate()
        return_code = proc.returncode
        if return_code != 0:
            logger.error("[sortinghat] Error in command %s", cmd)
        return return_code

    def do_affiliate(self):
        cmd = self.__build_sh_command()
        cmd += ['affiliate']
        self.__execute_sh_command(cmd)
        return

    def do_autogender(self):
        cmd = self.__build_sh_command()
        cmd += ['autogender']
        self.__execute_sh_command(cmd)
        return None

    def do_autoprofile(self, sources):
        cmd = self.__build_sh_command()
        cmd += ['autoprofile'] + sources
        self.__execute_sh_command(cmd)
        return None

    def do_unify(self, kwargs):
        cmd = self.__build_sh_command()
        cmd += ['unify', '--fast-matching', '-m', kwargs['matching']]
        if not kwargs['strict_mapping']:
            cmd += ['--no-strict-matching']
        self.__execute_sh_command(cmd)
        return

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

        uuids_refresh = []

        for algo in cfg['sortinghat']['matching']:
            if not algo:
                # cfg['sortinghat']['matching'] is an empty list
                logger.debug('Unify not executed because empty algorithm')
                continue
            kwargs = {'matching': algo, 'fast_matching': True,
                      'strict_mapping': cfg['sortinghat']['strict_mapping']}
            logger.info("[sortinghat] Unifying identities using algorithm %s",
                        kwargs['matching'])
            self.do_unify(kwargs)

        if not cfg['sortinghat']['affiliate']:
            logger.debug("Not doing affiliation")
        else:
            # Global enrollments using domains
            logger.info("[sortinghat] Executing affiliate")
            self.do_affiliate()

        if 'autoprofile' not in cfg['sortinghat'] or \
                not cfg['sortinghat']['autoprofile'][0]:
            logger.info("[sortinghat] Autoprofile not configured. Skipping.")
        else:
            logger.info("[sortinghat] Executing autoprofile for sources: %s",
                        cfg['sortinghat']['autoprofile'])
            sources = cfg['sortinghat']['autoprofile']
            self.do_autoprofile(sources)

        if 'autogender' not in cfg['sortinghat'] or \
                not cfg['sortinghat']['autogender']:
            logger.info("[sortinghat] Autogender not configured. Skipping.")
        else:
            logger.info("[sortinghat] Executing autogender")
            self.do_autogender()

        with TasksManager.IDENTITIES_TASKS_ON_LOCK:
            TasksManager.IDENTITIES_TASKS_ON = False
