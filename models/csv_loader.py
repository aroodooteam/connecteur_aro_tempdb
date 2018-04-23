# -*- coding: utf-8 -*-
# !/usr/bin/python


from openerp import models, api, fields, exceptions, _
from datetime import datetime
import os
import csv
import timeit
from . import connecteur as cn
# codeAg = cn.code_sa + code_gra
# import shutil
import logging
_logger = logging.getLogger(__name__)


# import sys  # , getopt
# import psycopg2
# import xmlrpclib

def splitList(arr, size):
    """
    Split long list in sublist
    """
    arrs = []
    while len(arr) > size:
        pice = arr[:size]
        arrs.append(pice)
        arr = arr[size:]
    arrs.append(arr)
    return arrs


def addElementInTuple(arr, elt):
    """
    :param list arr: The list to manipulate
    arr format -> [(x,x,{}), (x,x,{}), (x,x,{})]
    :param dict elt: The element to insert
    """
    arrs = []
    for tpl in arr:
        tpl[2].update(elt)
        arrs.append(tpl)
    return arrs


"""
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
"""


class CsvLoader(models.Model):
    _name = 'csv.loader'
    _description = 'Load csv file'

    name = fields.Char(string='Name', required=True)
    csv_path = fields.Char(string='Full path to csv file', required=True)
    with_header = fields.Boolean(string='Header', help='Contain header')
    delimiter = fields.Char(string='Separator', default=',',
                            help='Specify the separator', required=True)
    map_data = fields.Char(string='Map',
                           help='Map is a dict that will be use to fit \
                           column in database')
    cbm_ids = fields.One2many('csv.base.model', 'csv_loader_id',
                              string='Base Models')

    @api.multi
    def get_imported_field(self):
        res = []
        for cbm_id in self.cbm_ids:
            res += cbm_id.mapset_ids.mapped('map_fld')
        return res

    @api.multi
    def checkLine(self, line):
        if not line:
            return False
        # map_set_obj = self.env['csv.map.setting']
        # new_line = {}
        fld_use = self.get_imported_field()
        _logger.info('=== res = %s ===' % fld_use)
        for cbm_id in self.cbm_ids:
            model_obj = self.env[cbm_id.model]
            domain = cbm_id.compute_domain(line)
            if domain:
                model_src = model_obj.search(domain)
                _logger.info('=== model_src = %s ===' % model_src)
                cbm_id.check_create_or_update(model_src, line)
            # _logger.info('=== model_obj = %s ===' % model_obj)
            # _logger.info('=== domain = %s ===' % domain)

    @api.multi
    def checkPartnerAccount(self):
        account_obj = self.env['account.account']
        res = {
            'property_account_receivable': account_obj.search(
                [('code', '=', '410000')]).id,
            'property_account_payable': account_obj.search(
                [('code', '=', '463100')]).id,
        }
        return res

    @api.multi
    def getCsvHeader(self, direct=False):
        big_st = timeit.default_timer()
        if not os.path.exists(self.csv_path):
            raise exceptions.Warning(_('Error'),
                                     _('Wrong path !\n%s' % self.csv_path))
        move = self.env['account.move']
        total = 0
        partner_account = self.checkPartnerAccount()
        _logger.info('\n=== pacc = %s ===' % partner_account)
        move_line_dict = {}
        move_dict = {}
        with open(self.csv_path, 'rb') as csv_count:
            total = csv.DictReader(csv_count, delimiter=str(self.delimiter))
            total = len(list(total))
        with open(self.csv_path, 'rb') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=str(self.delimiter))
            if not direct:
                for line in reader:
                    self.checkLine(line)
            else:
                # move_line_dict = {}
                # move_dict = {}
                for i, line in enumerate(reader):
                    st = timeit.default_timer()
                    # _logger.info('=== read %d / %s ===' % (i+1, total))
                    # temporaire
                    line.update(partner_account)
                    self.normalizeLine(line)
                    self.checkAgency(line)
                    self.checkPeriod(line)
                    self.checkJournal(line)
                    self.checkAccount(line)
                    if self.is_apporteur(line):
                        self.checkApporteur(line)
                    else:
                        self.checkPartner(line)
                    self.prepareMoveLine(line)
                    self.groupMoveLine(line, move_line_dict)
                    self.prepareMove(line)
                    self.groupMove(line, move_dict)
                    elp = timeit.default_timer() - st
                    _logger.info('=== read %d / %s => %f sec ===' % (i+1, total, elp))
        if move_dict and move_line_dict:
            self.fullMove(move_dict, move_line_dict)
            del move_line_dict
            fullMove = len(move_dict)
            c = 0
            for k, v in move_dict.iteritems():
                c += 1
                _logger.info('=== piece %d / %s ===' % (c, fullMove))
                st_create = timeit.default_timer()
                line_ids = v.pop('line_id')
                move_id = move.search([('ref', '=', k)])
                if not move_id:
                    move_id = move.create(v)
                line_ids = addElementInTuple(line_ids, {'move_id': move_id.id})
                line_ids = splitList(line_ids, 150)
                fullLine = len(line_ids)
                for i, line_id in enumerate(line_ids):
                    _logger.info('==== ECR %d / %s ===' % (i+1, fullLine))
                    try:
                        move_id.write({'line_id': line_id})
                    except Exception, exc:
                        _logger.info('=== Skip MAJ impossible = {} ==='.format(exc))
                try:
                    move_id.button_validate()
                except Exception, e:
                    _logger.info('=== Err comptabilisation = {} ==='.format(e))
                elp_create = timeit.default_timer() - st_create
                _logger.info('=== piece full elapsed_time = %f ===' % elp_create)
            del move_dict
        total_time = timeit.default_timer() - big_st
        _logger.info('=== Migration Terminer en %f ===' % total_time)
        return True

    @api.multi
    def sqlMove(self, move_dict, move_line_dict):
        for k, v in move_dict.iteritems():
            mv_dict = move_dict.get(k)
            mvl_list_dict = move_line_dict.get(k)
            mv_dict['state'] = 'draft'
            mv_dict['company_id'] = 1
            if mv_dict.get('date', False):
                mv_dict['date'] = mv_dict.get('date').strftime('%d/%m/%Y')
            qry_mv = "insert into account_move (%s) values %s RETURNING id;" % (','.join(mv_dict.keys()), tuple(mv_dict.values()))
            _logger.info('=== qry_mv = %s ===' % qry_mv)
            self._cr.execute(qry_mv)
            # move_id = self._cr.fetchone()
            # _logger.info('=== qry_mv_id = %s ===' % self._cr.fetchone())
            for mvl in mvl_list_dict:
                mvl['company_id'] = 1
                if mvl.get('emp_effet', False):
                    mvl['emp_effet'] = mvl.get('emp_effet').strftime('%d/%m/%Y')
                if mvl.get('emp_datech', False):
                    mvl['emp_datech'] = mvl.get('emp_datech').strftime('%d/%m/%Y')

    @api.multi
    def groupMoveLine(self, line, move_line_dict):
        move_line = line.get('move_line', {})
        move_ref = line.get('move_ref', False)
        # _logger.info('\n=== move_line = %s === \n' % move_line)
        # search if line allready exist
        # ============TEST============
        # sql = """
        # select id from account_move_line where emp_as400_ses = '{}' and emp_as400_pie = '{}'
        # and emp_as400_lig = '{}';
        # """.format(move_line.get('emp_as400_ses'), move_line.get('emp_as400_pie'),
        #            move_line.get('emp_as400_lig'))
        # #_logger.info('=== sql = %s ===' % sql)
        # self._cr.execute(sql)
        # mvl_id = self._cr.fetchone()
        # _logger.info('=== mvl_id = %s ===' % mvl_id)
        # ============END TEST============
        # ============RETEST============
        mvl_id = False
        # sql = """
        # select id from account_move_line where emp_as400_ses = %s and emp_as400_pie = %s
        # and emp_as400_lig = %s;
        # """
        # self._cr.execute(sql, tuple((move_line.get('emp_as400_ses'), move_line.get('emp_as400_pie'),move_line.get('emp_as400_lig'))))
        # mvl_id = self._cr.fetchone()
        #_logger.info('=== mvl_id = %s ===' % mvl_id)
        if not mvl_id and move_ref not in move_line_dict.keys():
            move_line_dict[move_ref] = [(0, 0, move_line)]
        elif not mvl_id and move_ref in move_line_dict.keys():
            move_line_dict.get(move_ref).append((0, 0, move_line))
        elif mvl_id and move_ref not in move_line_dict.keys():
            move_line_dict[move_ref] = [(1, mvl_id, move_line)]
        else:
            move_line_dict.get(move_ref).append((1, mvl_id, move_line))
        # ============END RETEST============
        # mvl_id = False
        # # if you run it only once comment search to get faster
        # domain = [
        #     ('ref', '=', line.get('move_ref')),
        #     ('emp_as400_ses', '=', move_line.get('emp_as400_ses')),
        #     ('emp_as400_pie', '=', move_line.get('emp_as400_pie')),
        #     ('emp_as400_lig', '=', move_line.get('emp_as400_lig')),
        # ]
        # mvl_id = self.env['account.move.line'].search(domain)
        # if not mvl_id and move_ref not in move_line_dict.keys():
        #     move_line_dict[move_ref] = [(0, 0, move_line)]
        # elif not mvl_id and move_ref in move_line_dict.keys():
        #     move_line_dict.get(move_ref).append((0, 0, move_line))
        # elif mvl_id and move_ref not in move_line_dict.keys():
        #     move_line_dict[move_ref] = [(1, mvl_id.id, move_line)]
        # else:
        #     move_line_dict.get(move_ref).append((1, mvl_id.id, move_line))

    @api.multi
    def groupMove(self, line, move_dict):
        if line.get('move_ref', False) not in move_dict.keys():
            move_dict[line.get('move_ref', False)] = line.get('move')

    @api.multi
    def fullMove(self, move_dict, move_line_dict):
        for k in move_dict.keys():
            move_dict.get(k)['line_id'] = move_line_dict.get(k)

    # Import like connecteur, without setting parameter
    @api.multi
    def checkPeriod(self, value):
        if not value:
            return False
        periode = value.get('Periode', False)
        if not periode:
            return False
        journal_code = value.get('journal', False)
        if journal_code and journal_code.startswith('AN'):
            periode = '00/' + str(periode.split('/')[1])
        elif journal_code and journal_code.startswith('XX'):
            periode = '00/' + str(periode.split('/')[1])
        sql = "select id from account_period where code=%s"
        self._cr.execute(sql, tuple((periode,)))
        period_id = self._cr.dictfetchall()
        period_id = period_id[0].get('id')
        period_obj = self.env['account.period']
        #period_id = period_obj.search(
            #[('code', '=', periode)])
        #value['Periode'] = period_id.id
        value['Periode'] = period_id
        return period_obj.browse(period_id)

    @api.multi
    def checkJournal(self, value):
        if not value:
            return False
        if not value.get('journal', False):
            return False
        sql = "select id from account_journal where code=%s"
        self._cr.execute(sql, tuple((value.get('journal'),)))
        journal_id = self._cr.dictfetchall()
        journal_id = journal_id[0].get('id')
        journal_obj = self.env['account.journal']
        # journal_id = journal_obj.search(
        #     [('code', '=', value.get('journal', False))])
        if not journal_id:
            raise exceptions.Warning(_('Error'), _('journal %s not found' % value.get('journal', False)))
        # value['journal'] = journal_id.id
        value['journal'] = journal_id
        return journal_obj.browse(journal_id)

    @api.multi
    def checkAccount(self, value):
        if not value:
            return False
        if not value.get('Compte', False):
            return False
        sql = "select id from account_account where code=%s"
        self._cr.execute(sql, tuple((value.get('Compte'),)))
        account_id = self._cr.dictfetchall()
        account_obj = self.env['account.account']
        # account_id = account_obj.search(
        #     [('code', '=', value.get('Compte', False))])
        if not account_id:
            _logger.info('=== Erreur: account %s not found ===' % value.get('Compte', False))
            raise exceptions.Warning(_('Error'), _('account not found %s' % value.get('Compte', False)))
        account_id = account_id[0].get('id')
        value['Compte'] = account_id
        #value['Compte'] = account_id.id
        return account_obj.browse(account_id)

    @api.multi
    def checkAgency(self, value):
        if not value:
            return False
        ag = value.get('Agence', False)
        agence = False
        if ag and ag not in cn.code_sa:
            sql = "select id from base_agency where code=%s"
            self._cr.execute(sql, tuple((str(ag),)))
            agence_req = self._cr.dictfetchall()
            agence = agence_req[0].get('id')
            #agence = self.env['base.agency'].search([('code', '=', ag)])
        if not agence:
            return False
        value['Agence'] = agence
        #value['Agence'] = agence.id

    @api.multi
    def normalizeLine(self, line):
        for k, v in line.iteritems():
            if v == '':
                line[k] = False
            if k in ['Date', 'Effet', 'Emission', 'DatFAct', 'DatEch']:
                if line.get(k):
                    line[k] = self.normalizeDate(line.get(k))
        jrnl = line.get('journal', False)
        prd = line.get('Periode', False).split('/')[1]
        ses = line.get('AS400_ses', False)
        pie = line.get('AS400_pie', False)
        line['move_ref'] = 'ECR/%s/%s/%s/%s' % (jrnl, prd, ses, pie)

    @api.multi
    def normalizeDate(self, date_value):
        if not date_value:
            return False
        if len(date_value.split('/')) == 2:
            if int(date_value.split('/')[0]) == 0:
                date_value = '01/%s' % date_value.split('/')[1]
            elif int(date_value.split('/')[0]) > 12:
                date_value = '12/%s' % date_value.split('/')[1]
            date_value = '01/%s' % date_value
        try:
            date_value = datetime.strptime(date_value, '%d/%m/%Y')
            return date_value
        except Exception, e:
            _logger.info('=== error_converting_date %s = %s ===' % (date_value, str(e)))

    @api.multi
    def is_apporteur(self, line):
        if not line:
            return False
        ref = line.get('Code_tiers', False)
        if not ref:
            return False
        return ref[:5].endswith('2')

    @api.multi
    def checkApporteur(self, line):
        if not line.get('Code_tiers', False):
            return False
        ref = line.get('Code_tiers', False)
        sql = "select id,partner_id from res_apporteur where ref_apporteur=%s"
        self._cr.execute(sql, tuple((ref,)))
        apporteur = self._cr.dictfetchall()
        if apporteur:
            apporteur = self.env['res.apporteur'].browse(apporteur[0].get('id'))
        #apporteur = self.env['res.apporteur'].search([('ref_apporteur', '=', ref)])
        if not apporteur:
            vals = {
                'name': line.get('Partenaire', 'PARTENAIRE %s' % ref),
                'agency_id': line.get('Agence', False),
                'ref_apporteur': ref,
                'serial_identification': ref[-3:],
            }
            apporteur = self.env['res.apporteur'].create(vals)
        if apporteur:
            line.pop('Partenaire')
            line.pop('Code_tiers')
            #line['partner_id'] = apporteur[0].get('partner_id')
            line['partner_id'] = apporteur.partner_id.id
            return apporteur.partner_id.id
            #return apporteur[0].get('partner_id')
        else:
            vals = {
                'name': '',
                'agency_id': '',
                'ref_apporteur': '',
            }
            self.env['res.apporteur'].create(vals)
        # _logger.info('\n=== End checkApporteur ===\n')
        return False

    @api.multi
    def checkPartner(self, value):
        if not value:
            return False
        ref = value.get('Code_tiers', False)
        if ref in ['', False]:
            ref = False
        name = value.get('Partenaire', False)
        if not ref and not name:
            return False
        partner_obj = self.env['res.partner']
        partner_id = False
        if ref:
            sql = "select id from res_partner where ref=%s"
            self._cr.execute(sql, tuple((ref,)))
            partner_id = self._cr.dictfetchall()
            #partner_id = partner_obj.search([('ref', '=', ref)])
        if name and not partner_id:
            sql2 = "select id,name,title from res_partner where name ilike %s"
            #sql2 = "select id,name,property_account_receivable,property_account_payable,title from res_partner where name ilike %s"
            self._cr.execute(sql2, tuple((name,)))
            partner_ref = self._cr.dictfetchall()
            #partner_ref = partner_obj.search([('name', 'ilike', name)])
            vals = {}
            if not partner_ref:
                vals = {
                    'name': name,
                    'property_account_receivable': value.get('property_account_receivable', False),
                    'property_account_payable': value.get('property_account_payable', False),
                    'title': False,
                    'ref': ref,
                    'customer': True,
                    'comment': 'ECR',
                }
            else:
                # if len(partner_ref) > 1:
                #     partner_ref = partner_ref[0]
                partner_ref = partner_ref[0]
                part_id = partner_obj.browse(partner_ref.get('id'))
                vals = {
                    'name': partner_ref.get('name'),
                    'property_account_receivable': part_id.property_account_receivable,
                    'property_account_payable': part_id.property_account_payable,
                    'title': partner_ref.get('title'),
                    'ref': ref,
                    'customer': True,
                    'comment': 'ECR',
                }
                # vals = {
                #     'name': partner_ref.name,
                #     'property_account_receivable': partner_ref.property_account_receivable,
                #     'property_account_payable': partner_ref.property_account_payable,
                #     'title': partner_ref.title.id if partner_ref.title else False,
                #     'ref': ref,
                #     'customer': True,
                #     'comment': 'ECR',
                # }
            partner_id = partner_obj.create(vals)
        partner_id = partner_id[0].get('id') if isinstance(partner_id, list) else partner_id.id
        value['partner_id'] = partner_id
        #value['partner_id'] = partner_id.id
        value.pop('Partenaire')
        value.pop('Code_tiers')
        # _logger.info('=== End checkPartner ===')
        return partner_obj.browse(partner_id)

    @api.multi
    def checkMove(self, value):
        """
            :param Dict value: compiled value from previous function
        """
        if not value:
            return False
        journal_id = value.get('journal_id', False)
        period_id = value.get('period_id', False)
        date = value.get('date', False)
        ref = value.get('ref', False)
        if not journal_id or not period_id:
            return False
        if not ref:
            return False
        year = str(period_id.code).split('/')[1]
        ref = 'ECR/%s/%s/%s' % (journal_id.code, year, ref)
        # ECR/code_journal/annee/pie/ses
        move_obj = self.env['account.move']
        move_id = move_obj.search([('ref', '=', ref)])
        if not date:
            date = '01/%s' % (period_id.code)
        date = datetime.strptime(date, '%d/%m/%Y')
        vals = {
            'name': ref,
            'ref': ref,
            'journal_id': journal_id.id,
            'period_id': period_id.id,
            'date': date,
        }
        if not move_id:
            move_id = move_obj.create(vals)
        else:
            move_id.update(vals)
        return move_id

    @api.multi
    def prepareMoveLine(self, line):
        vals = {
            'name': line.get('Description', '/'),
            'account_id': line.get('Compte', False),
            'emp_police': line.get('Police', False),
            'emp_quittance': line.get('Quittance', False),
            'emp_effet': line.get('Effet', False),
            'emp_datech': line.get('DatEch', False),
            'partner_id': line.get('partner_id', False),
            'debit': line.get('Debit', 0.0).replace(',', '.'),
            'credit': line.get('Credit', 0.0).replace(',', '.'),
            'emp_libana': line.get('LibAna', False),
            'emp_as400_compte': line.get('AS400_Compte', False),
            'emp_as400_pie': line.get('AS400_pie', False),
            'emp_as400_ses': line.get('AS400_ses', False),
            'emp_as400_lig': line.get('AS400_lig', False),
            'emp_fluxtres': line.get(u'FluxTrés', False),
            'narration': 'ECR',
            'period_id': line.get('Periode', False),
            'journal_id': line.get('journal', False),
            'ref': line.get('move_ref', False),
            'emp_folio': line.get('Folio', False),
        }
        line['move_line'] = vals

    @api.multi
    def prepareMove(self, line):
        move_data = {
            'journal_id': line.get('journal', False),
            'period_id': line.get('Periode', False),
            'date': line.get('Date', False),
            'ref': line.get('move_ref', False),
            'name': line.get('move_ref', False),
            'narration': line.get('move_ref', False)
        }
        line['move'] = move_data

    @api.multi
    def checkLineDict(self, line):
        effet = line.get('Effet', False)
        ech = line.get('DatEch', False)
        date = line.get('Date', False)
        if effet and effet != '':
            if int(effet.split('/')[0]) == 0:
                effet = '01/%s' % effet.split('/')[1]
            elif int(effet.split('/')[0]) > 12:
                effet = '12/%s' % effet.split('/')[1]
            effet = '01/%s' % effet
            effet = datetime.strptime(effet, '%d/%m/%Y')
        elif effet == '':
            effet = False
        if ech == '':
            ech = False
        if ech:
            ech = datetime.strptime(ech, '%d/%m/%Y')
        account_id = self.checkAccount(line)
        account_id = account_id.id if account_id else False
        move_data = {}
        partner_id = self.checkPartner(line)
        journal_id = self.checkJournal(line)
        period_id = self.checkPeriod(line)
        emp_as400_pie = line.get('AS400_pie', False)
        emp_as400_ses = line.get('AS400_ses', False)
        move_data = {
            'partner_id': partner_id if partner_id else False,
            'journal_id': journal_id if journal_id else False,
            'period_id': period_id if period_id else False,
            'date': date,
            'ref': '%s/%s' % (emp_as400_pie, emp_as400_ses),
        }
        move_id = self.checkMove(move_data)
        vals = {
            'name': line.get('Description', '/'),
            'account_id': account_id,
            'emp_police': line.get('Police', False),
            'emp_quittance': line.get('Quittance', False),
            'emp_effet': effet,
            'emp_datech': ech,
            'partner_id': partner_id.id if partner_id else False,
            'debit': line.get('Debit', 0.0).replace(',', '.'),
            'credit': line.get('Credit', 0.0).replace(',', '.'),
            'emp_libana': line.get('LibAna', False),
            'emp_as400_compte': line.get('AS400_Compte', False),
            'emp_as400_pie': emp_as400_pie,
            'emp_as400_ses': emp_as400_ses,
            'emp_as400_lig': line.get('AS400_lig', False),
            'emp_fluxtres': line.get(u'FluxTrés', False),
            'narration': 'ECR',
            'period_id': period_id.id if period_id else False,
            'journal_id': journal_id.id if journal_id else False,
            'ref': move_id.ref if move_id.ref else '',
            'move_id': move_id.id if move_id else False,
        }
        move_line_obj = self.env['account.move.line']
        move_line = move_line_obj.search([
            ('emp_as400_ses', '=', vals.get('emp_as400_ses')),
            ('emp_as400_pie', '=', vals.get('emp_as400_pie')),
            ('emp_as400_lig', '=', vals.get('emp_as400_lig')),
        ])
        if not move_line:
            move_line = move_line_obj.create(vals)
            move_line.update(vals)
        else:
            move_line.update(vals)
        return move_id

    @api.multi
    def importCsvFixedParam(self):
        self.getCsvHeader(True)
        return True


"""
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
    writer = csv.writer(csvfile,  delimiter=', ')
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
"""
