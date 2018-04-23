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
#     Alvaro del Castillo <acs@bitergia.com>
#

import logging
import os
import shutil
import subprocess
import tempfile

from datetime import date, timedelta, timezone
from distutils.dir_util import copy_tree

from dateutil import parser

from manuscripts.report import Report

from sirmordred.task import Task

logger = logging.getLogger(__name__)


class TaskReport(Task):
    """ Task to generate the PDF report for the project """

    def __init__(self, conf):
        super().__init__(conf)

    def is_backend_task(self):
        return False

    def execute(self):
        cfg = self.conf

        global_project = cfg['general']['short_name']
        elastic = cfg['es_enrichment']['url']
        data_dir = cfg['report']['data_dir']
        end_date = cfg['report']['end_date']
        start_date = cfg['report']['start_date']
        offset = cfg['report']['offset']
        config_file = cfg['report']['config_file']
        interval = cfg['report']['interval']
        filters = cfg['report']['filters']

        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

        # All the dates must be UTC, including those from command line
        if end_date == 'now':
            end_date = parser.parse(date.today().strftime('%Y-%m-%d')).replace(tzinfo=timezone.utc)
        else:
            end_date = parser.parse(end_date).replace(tzinfo=timezone.utc)
        # The end date is not included, the report must finish the day before
        end_date += timedelta(microseconds=-1)
        start_date = parser.parse(start_date).replace(tzinfo=timezone.utc)

        offset = offset if offset else None

        report = Report(elastic, start=start_date,
                        end=end_date, data_dir=data_dir,
                        filters=Report.get_core_filters(filters),
                        interval=interval,
                        offset=offset,
                        config_file=config_file)
        report.create()

        # First copy the reports template to create a new report from it
        tmp_path = tempfile.mkdtemp(prefix='report_')
        copy_tree("reports/report_template", tmp_path)
        # Copy the data generated to be used in LaTeX template
        copy_tree("report_data", os.path.join(tmp_path, "data"))
        copy_tree("report_data", os.path.join(tmp_path, "figs"))
        # Change the project global name
        cmd = ['sed -i s/TemplateProject/' + global_project + '/g *.tex']
        subprocess.call(cmd, shell=True, cwd=tmp_path)
        # Fix LaTeX special chars
        cmd = [r'sed -i "s/\&/\\\&/g" data/git_top_organizations_*']
        subprocess.call(cmd, shell=True, cwd=tmp_path)
        # Build the report
        subprocess.call("make", shell=True, cwd=tmp_path)
        # Copy the report
        copy_tree(os.path.join(tmp_path, "pdf"), "report_data/pdf")
        shutil.rmtree(tmp_path)
