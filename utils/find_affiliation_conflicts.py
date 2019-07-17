#!/usr/bin/env python
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

import MySQLdb

host = "localhsot"
user = "root"
password = ""
name = "sortinghat_sh"
db = MySQLdb.connect(host, user, password, name)

cursor = db.cursor()
# get all uuid with more than 1 affiliation
cursor.execute("select * from (select uuid, count(*) as total from enrollments group by uuid) b where b.total>1;")


rows = cursor.fetchall()
for r in rows:
    uuid = str(r[0])
    # group by start,end date for uuids with more than 1 affilation
    cursor.execute("SELECT COUNT(*), start, end FROM enrollments WHERE uuid = '%s' GROUP BY start,end" % uuid)
    data = cursor.fetchone()
    total = data[0]
    start = data[1]
    end = data[2]
    if data[0] > 1:
        # conflict identified, gets organization names and uuid to compose the log
        cursor.execute("SELECT organizations.name FROM enrollments, organizations WHERE start = '%s' "
                       " AND end = '%s' AND uuid = '%s' AND organization_id = organizations.id" % (start, end, uuid))
        data = cursor.fetchall()
        orgs = []
        for o in data:
            orgs.append(o[0])
        orgs.sort()
        print("%s affiliation conflict with orgs %s" % (uuid, str(orgs)))

# disconnect from server
db.close()
