# -*- coding: utf-8 -*-
# !/usr/bin/python

import sys  # , getopt
import psycopg2
import csv
import xmlrpclib

username = 'admin'
dbuser = 'aroodoo'
dbpwd = 'aroodoo'
pwd = 'admin'
dbname = 'aro_007'
host = 'localhost'
port = '8069'
sock_common = xmlrpclib.ServerProxy('http://' + host +
                                    ':' + port + '/xmlrpc/common')
uid = sock_common.login(dbname,  username,  pwd)
sock = xmlrpclib.ServerProxy('http://' + host + ':' + port + '/xmlrpc/object')

csv_file_name = sys.argv[1]
count = 0
skip_rows = 0
many2one = []
model_map = {}
model_map['period_id'] = ['account.period', 'code', [], {}]
model_map['move_id'] = ['account.move', 'ref', [], {}]
model_map['account_id'] = ['account.account', 'code', [], {}]
model_map['journal_id'] = ['account.journal', 'code', [], {}]
model_map['partner_id'] = ['res.partner', 'ref', [], {}]
# model_map['currency_id'] = ['res.currency', 'name', [], {}]

map = {}

object_name_from_file = csv_file_name.split('.')
create_obj = ''
table_name = ''
for name in object_name_from_file:
    if name != 'csv':
        if create_obj != '':
            create_obj += '.'
        create_obj += name
for name in object_name_from_file:
    if name != 'csv':
        if table_name != '':
            table_name += '_'
        table_name += name

with open(csv_file_name,  'rb') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    rows = 7155
    print 'Reading...'
    for row in reader:
        count += 1
        if count == 1:
            header = row
            head_count = 0
            for h in header:
                if '_id' in h:
                    many2one.append(head_count)
                head_count += 1
        else:
            for pos in many2one:
                if row[pos] not in model_map[header[pos]][2]:
                    model_map[header[pos]][2].append(row[pos])
                    # ids = sock.execute(dbname, uid, pwd,
                    # model_map[header[pos]][0],  'search',  args)
                    # map[row[pos]]=ids
    print 'Searching...'
    for model in model_map:
        result = {}
        obj = model_map[model][0]
        crit = model_map[model][1]
        vals = model_map[model][2]
        print obj
        args = [(crit, 'in', vals)]
        ids = sock.execute(dbname,  uid,  pwd,  obj,  'search',  args)
        reads = sock.execute(dbname, uid, pwd, obj, 'read', ids, [crit])
        for read in reads:
            result[read[crit]] = read['id']
        model_map[model][3] = result
    print 'Writing Excel'
    count = 0
skip = []
data = []
with open(csv_file_name,  'rb') as csvfile:
    reader = csv.reader(csvfile, delimiter=', ')
    for row in reader:
        count += 1
        if count > 1:
            error = False
            for pos in many2one:
                try:
                    row[pos] = model_map[header[pos]][3][row[pos]]
                except KeyError:
                    error = True
                    skip.append(row)
                    break
            if not error:
                data.append(row)
with open('skipped.csv',  'wb') as csvfile:
    print 'Creating skip file...'
    writer = csv.writer(csvfile,  delimiter=',')
    for s in skip:
        writer.writerow(s)


if len(skip) == 0:
    with open('to_load.csv',  'wb') as csvfile:
        print 'Creating data file...'
        writer = csv.writer(csvfile,  delimiter=', ')
        created = 0
        values = {'currency_id': False, 'amount_currency': 0}
        for d in data:
            writer.writerow(d)
        # count=0
        # while count<len(header):
            # values[header[count]]=d[count]
            # count+=1
        # print values
        # ids = sock.execute(dbname, uid, pwd, create_obj, 'create', values)
        # created+=1
        # print 'Creating :' + str((rows-created)/rows*100) + '%'
    conn_string = "host='" + host + "' dbname='" + dbname \
        + "' user='" + dbuser + "' password='" + dbpwd + "'"
    print "Connecting to database\n ->%s" % (conn_string)
    conn = psycopg2.connect(conn_string)
    cursor = conn.cursor()
    print header
    with open('to_load.csv',  'rb') as csvfile:
        print 'loading...'
        data_load = cursor.copy_from(csvfile, table_name,
                                     sep=',', columns=header)
        conn.commit()
        sql = "SELECT id, ref from account_move_line where move_id=570;"
        cursor.execute(sql)
        reads = cursor.fetchall()
        print reads
    print 'Done!'
    conn_2 = psycopg2.connect(conn_string)
    cursor_2 = conn_2.cursor()
    sql_2 = "UPDATE account_move_line set state='valid';"
    cursor_2.execute(sql_2)
    # conn_2.commit()
    print 'Updating : set state to valid and company_id to 1'
else:
    print 'Skip File Created,  no imports done'
