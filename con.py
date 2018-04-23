# -*- coding: utf-8 -*-
# import pypyodbc
import pyodbc
import logging
_logger = logging.getLogger(__name__)

code_gra = ('07', '19', '27', '28', '30', '74', '80', '85', '86', '93')
code_sa = ('01', '06', '15', '17', '38', '42', '43', '45', '51', '52',
           '71', '87')

try:
    print "try to connect"
    # con = pypyodbc.connect("DRIVER=FreeTDS;SERVER=10.0.0.92;PORT=1433;
    # DATABASE=dwh_stat;UID=sa;PWD=Aro1;TDS_Version=7.0")
    prm = "DRIVER=FreeTDS;SERVER=10.0.0.92;PORT=1433;DATABASE=dwh_stat; \
            UID=sa;PWD=Aro1;TDS_Version=7.0"
    con = pyodbc.connect(prm)
    print "connected = %s" % con
    cursor = con.cursor()
    # sql = "select * from tdc where agence in %s" % str(code_gra)
    # sql = "select top 1 CODEAG, NUM_COMMAG, COURTIER1, COURTIER2 from \
    # tempdb_odoo where CODEAG in %s and AACPT=2015 \
    # and MMCPT='01'" % str(code_gra)
    # sql = "select new,titre,nom,prenom,statut from tdc where agence='%s' and old='%s' " % ('01','000')
    sql = "select new,titre,nom,prenom,statut,agence from tdc where agence in %s" % (str(code_sa))
    sqlb = """select CODEAG, NUM_COMMAG, COURTIER1, COURTIER2 from tempdb_odoo
    where CODEAG not in %s and AACPT=2015 and MMCPT='01'""" % str(code_gra + code_sa)
    sqla = """select * from tempdb_odoo
    where CODEAG in %s and AACPT=2015 and MMCPT='01'""" % str(code_sa)
    print sql
    cursor.execute(sql)
    columns = [column[0] for column in cursor.description]
    # print("=== columns = %s ===" % columns)

    line_cnt = 1
    for row in cursor:
        cnt = 0
        data = {}
        for col in columns:
            data[col] = row[cnt]
            cnt += 1
        print('%s === data = %s ===' % (line_cnt, data))
        line_cnt += 1
    con.close()
    print "disconnected = %s" % con
except Exception, e:
    print e
