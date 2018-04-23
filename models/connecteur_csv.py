# -*- coding: utf-8 -*-
###############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2015-Today NextHope Business Solutions
#    <contact@nexthope.net>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###########################################################################
from openerp import models, api, fields, exceptions, _
import os
from datetime import datetime
import decimal
# import pyodbc
import logging
import csv
import timeit

_logger = logging.getLogger(__name__)

code_gra = ['02', '07', '19', '27', '28', '30', '74', '80', '85', '86', '93']
code_sa = [
    '01', '04', '05', '06', '09', '10', '12', '13', '15', '17', '1T', '21',
    '22', '23', '25', '26', '29', '2D', '31', '33', '34', '37', '38', '39',
    '3F', '42', '43', '44', '45', '46', '47', '48', '49', '4M', '51', '52',
    '54', '55', '56', '57', '5A', '60', '62', '63', '64', '65', '67', '68',
    '69', '6U', '71', '72', '73', '75', '76', '82', '83', '87', '88', '89',
    '98']
# sous_agence : agence
map_code_sa = {
    '09': '99', '1T': '11', '60': '50', '62': '61', '63': '61', '64': '61',
    '65': '18', '67': '03', '68': '18', '69': '03', '5A': '61', '25': '20',
    '26': '20', '21': '20', '22': '20', '23': '20', '29': '20', '2D': '50',
    '98': '11', '10': '99', '13': '11', '12': '99', '15': '11', '17': '11',
    '55': '53', '54': '53', '57': '50', '56': '50', '51': '50', '52': '50',
    '6U': '32', '88': '99', '89': '40', '82': '11', '83': '20', '87': '40',
    '01': '18', '06': '11', '04': '11', '49': '40', '46': '40', '47': '50',
    '44': '40', '45': '40', '42': '11', '43': '40', '3F': '20', '76': '70',
    '75': '70', '4M': '40', '73': '16', '72': '16', '71': '70', '39': '20',
    '38': '32', '48': '50', '33': '03', '31': '11', '05': '11', '37': '11',
    '34': '11'}
map_gnrl = {}
map_app = {
    'agence': 'agency_id',
    'old': 'serial_identification',
    'new': 'ap_code',
    'titre': 'title',
    'name': 'name',
    'statut': 'statut'
}
request_sql = """ select top 10
                   codeag,courtier1,courtier2,
                   compte,titre,nom40,
                   numpol,dateeffet,dateecheance,codebranc,codecateg,vtable,
                   vdureectr,vdureepai,vmodepai,cpa,cpu,
                   numaven,aarattach,mmrattach,aacpt,mmcpt,codecarte,ordre,
                   codefic,num_primenet,num_access,num_te,num_tva,num_primetot,
                   num_commag,num_commcrt1,num_commcrt2,num_interav,
                   datecomptable,tmv
            from tempdb where  aacpt = 2015 """

request_sql2 = u"""
select
ID comment, default_code, NUMPOL , DATEEFFET prm_datedeb,
DATEECHEANCE prm_datefin,
rtrim(ltrim(MMCPT)) +'/'+rtrim(ltrim(str(AACPT))) period,
CODEAG, DATECOMPTABLE, ORDRE, COMPTE, TITRE, NOM40, ADRESSE1, ULIBELLE,
cast(NUM_COMMAG as float) NUM_COMMAG, COURTIER1, COURTIER2,
cast(NUM_COMMCRT1 as float) NUM_COMMCRT1,
cast(NUM_COMMCRT2 as float) NUM_COMMCRT2,
cast(NUM_PRIMENET as float) NUM_PRIMENET,
cast(NUM_ACCESS as float) NUM_ACCESS,
cast(NUM_TE as float) NUM_TE, cast(NUM_TVA as float) NUM_TVA,
cast(NUM_INTERAV as float) NUM_INTERAV
from tempdb_odoo_16
where AACPT=2016
and MMCPT = '01'
"""
# and ID=4270519
# and MMCPT = '01'
# ('01','02','03','04','05','06','07','08','09','10','11')
# and NUM_COMMAG < 0
# and CODEAG in ('02', '07') '17', '06'
map_sql2 = {
    'default_code': 'default_code',
    'COMMAG': 'serial_identification_ag',
    'NUM_COMMAG': 'commag_amount',
    'NUMPOL': 'pol_numpol',
    'DATEEFFET': 'prm_datedeb',
    'DATEECHEANCE': 'prm_datefin',
    'PERIOD': 'period',
    'CODEAG': 'agency_id',
    'DATECOMPTABLE': 'date_comptable',
    'ORDRE': 'ordre',
    'COMPTE': 'compte',
    'TITRE': 'title',
    'NOM40': 'name',
    'ADRESSE1': 'street',
    'ULIBELLE': 'city',
    'COURTIER1': 'serial_identification_a',
    'COURTIER2': 'serial_identification_b',
    'NUM_COMMCRT1': 'code_app_a',
    'NUM_COMMCRT2': 'code_app_b',
    'NUM_PRIMENET': 'price_unit',
    'NUM_ACCESS': 'access_amount',
    'NUM_TE': 'tax_te',
    'NUM_TVA': 'tax_tva',
    'NUM_INTERAV': 'interest_amount',
}



class ConnecteurCsv(models.Model):
    _name = 'connecteur.csv'

    name = fields.Char(string='Name', required=True)
    csv_path = fields.Char(string='Full path to csv file', required=True)
    with_header = fields.Boolean(string='Header', help='Contain header')
    delimiter = fields.Char(string='Separator', default=',',
                            help='Specify the separator', required=True)

    #----------------------------------
    @api.multi
    def start_import(self):
        # check csv path
        if not os.path.exists(self.csv_path):
            raise exceptions.Warning(_('Error'),
                                     _('Wrong path !\n%s' % self.csv_path))
        path_log = '/opt/aro/filestore/tempdb.csv'
        try:
            os.remove(path_log)
        except Exception, e:
            _logger.info('\n=== Exception = %s === \n' % e)
        total = 0
        acc_410000 = self.env['account.account'].search([('code', '=', '410000')])
        acc_411100 = self.env['account.account'].search([('code', '=', '411100')])
        journal_sale = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        cust_acc = self.get_customer_account()
        kwargs = {'acc_410000': acc_410000, 'acc_411100': acc_411100,
                  'journal_sale': journal_sale}
        fieldnames = []

        # check total line in csv
        with open(self.csv_path, 'rb') as csv_count:
            total = csv.DictReader(csv_count, delimiter=str(self.delimiter))
            total = len(list(total))
        # start map data
        with open(self.csv_path, 'rb') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=str(self.delimiter))
            # move_line_dict = {}
            # move_dict = {}
            for i, dpt_datas in enumerate(reader):
                to_log = dpt_datas.copy()
                # init fieldnames
                if not fieldnames:
                    fieldnames.append('bugs')
                    for k, v in dpt_datas.iteritems():
                        fieldnames.append(k)
                # end init
                st = timeit.default_timer()
                dpt_datas = self.map_specified_data(dpt_datas, map_sql2)
                # _logger.info('\n=== dpt_datas1= %s === \n' % dpt_datas)
                self.clean_data_to_update(dpt_datas)
                # _logger.info('=== dpt_datas2 = %s ===' % dpt_datas)
                dpt_datas = self.dispatch_mapped_data(dpt_datas, kwargs)
                # ********* temporaire *********
                com_list = []
                invoice_vals = {'partner_id': False, }
                px_ctg = dpt_datas.get('product').get('default_code')[:1]
                # ================================================
                # Check invoice
                # ================================================
                invoice_vals.update(dpt_datas.get('invoice'))
                # Check res_partner_title
                # partner_title = self.check_partner_title(dpt_datas.get('partner_title'))
                # ================================================
                # Check the right partner to use in invoice
                # ================================================
                # Check if customer exist
                part_cust = dpt_datas.get('partner_customer')
                self.patch_partner(dpt_datas, cust_acc, part_cust, com_list, invoice_vals, px_ctg)
                # _logger.info('=== com_list = %s ===' % com_list)
                if invoice_vals.get('partner_id', False):
                    invoice_vals['partner_id'] = invoice_vals.get('partner_id', False).id
                if invoice_vals.get('final_customer_id', False):
                    invoice_vals['final_customer_id'] = invoice_vals.get('final_customer_id', False).id
                invoice_id = self.check_invoice(invoice_vals)
                # ================================================
                # si des commission ont été défini avant la creation de la facture
                # alors mettre à jour le champ commission_invoice avec l'id de cette dernière
                # ================================================
                com_buf_list = []
                for com in com_list:
                    if not com.get('commission_invoice', False):
                        com['commission_invoice'] = invoice_id.id
                    com_buf_list.append(com)
                com_list = []
                com_list = com_buf_list
                # ================================================
                # Check apporteur
                # ================================================
                # TODO
                appa_id = False
                appa_dict = dpt_datas.get('partner_apporteur_a', False)
                if appa_dict:
                    appa_dict_a = appa_dict.copy()
                    appa_dict_a.pop('account_amount')
                    appa_id = self.check_partner_apporteur(appa_dict_a)
                appb_id = False
                appb_dict = dpt_datas.get('partner_apporteur_b', False)
                if appb_dict:
                    appb_dict_b = appb_dict.copy()
                    appb_dict_b.pop('account_amount')
                    appb_id = self.check_partner_apporteur(appb_dict_b)
                # ================================================
                # Check account for commission line
                # ================================================
                # TODO
                # replace fixed value 'CRT' by computed value
                # to check it if it's <CRT> or <GRA>
                if appa_id:
                    com_acca = self.check_account_apporteur('CRT', px_ctg)
                    account_amount_a = appa_dict.get('account_amount', 0.0)
                    com_list.append({
                        'partner_commissioned': appa_id.partner_id.id,
                        'account_amount': account_amount_a,
                        'account_commission': com_acca.get('account_commission', False),
                        'account_charge_commission': com_acca.get('account_charge_commission', False),
                        'commission_invoice': invoice_id.id})
                    # app_list.append(appa_id.id)
                if appb_id:
                    com_accb = self.check_account_apporteur('CRT', px_ctg)
                    account_amount_b = appb_dict.get('account_amount', 0.0)
                    com_list.append({
                        'partner_commissioned': appb_id.partner_id.id,
                        'account_amount': account_amount_b,
                        'account_commission': com_accb.get('account_commission', False),
                        'account_charge_commission': com_accb.get('account_charge_commission', False),
                        'commission_invoice': invoice_id.id})
                # _logger.info('=== com_list final = %s ===' % com_list)
                self.check_commission_apporteur_all(com_list)
                # =======================================================
                # Prepare invoice_line taxes
                # =======================================================
                # invoice_line_tax_id = {}
                taxes_list = []
                # Treatment of TE Rate
                invoice_line_tax_te = dpt_datas.get('tax_te')
                rate_te = self.get_rate_te(invoice_line_tax_te)
                if rate_te:
                    taxes_list.append(rate_te.id)
                else:
                    # insert in log
                    to_log['bugs'] = 'TE rate not found'
                    self.archivate_incorrect_data('tempdb.csv', fieldnames, to_log)
                    _logger.info('=== Next TE rate===')
                    continue
                # Treatment of TVA Rate
                invoice_line_tax_tva = dpt_datas.get('tax_tva')
                rate_tva = self.get_rate_tva(invoice_line_tax_tva)
                if not rate_tva.get('tva_id', False):
                    # insert in log
                    _logger.info('=== TVA rate not found ===')
                    to_log['bugs'] = 'TVA rate <%s> not found' % rate_tva.get('tva_code', '?')
                    self.archivate_incorrect_data('tempdb.csv', fieldnames, to_log)
                    _logger.info('=== Next TVA rate===')
                    continue
                rate_tva = self.track_corresponding_tva(rate_te, rate_tva.get('tva_id', False))
                if rate_tva.get('tax_id', False):
                    taxes_list.append(rate_tva.get('tax_id').id)
                else:
                    # insert in log
                    _logger.info('===bug rate_tva = %s ===' % rate_tva)
                    to_log['bugs'] = 'Corresponding TVA <%s / %s> rate not found' % (rate_tva.get('te_amount'), rate_tva.get('tva_amount'))
                    self.archivate_incorrect_data('tempdb.csv', fieldnames, to_log)
                    _logger.info('=== Next Corresponding TVA rate===')
                    continue

                invoice_line_tax_id = [(6, 0, taxes_list)]
                # =======================================================
                # Prepare invoice_line data
                # =======================================================
                invoice_lines = dpt_datas.get('invoice_line')
                self.patch_invoice_lines(invoice_lines, invoice_id, rate_te, invoice_line_tax_id)
                # recompute_taxe
                invoice_id.button_reset_taxes()

                # reset type of invoice if amount_total < 0
                put_to_out_refund = False
                if invoice_id.amount_total < 0:
                    put_to_out_refund = True
                elif invoice_id.amount_total == 0:
                    for com_id in invoice_id.commission_ids:
                        if com_id.account_amount < 0 and put_to_out_refund is not True:
                            _logger.debug('=== put to out_refund ===')
                            put_to_out_refund = True

                if put_to_out_refund:
                    _logger.info('=== reset type invoice and account ===')
                    journal_id = invoice_id.journal_id
                    jrn_code = journal_id.code
                    if jrn_code.startswith('P'):
                        jrn_code = 'V' + jrn_code[1:]
                    jrn_id = self.env['account.journal'].search([('code', '=', jrn_code)])
                    if not jrn_id:
                        raise exceptions.Warning(_('Error'), _('Journal with code <%s> doesn\'t exist' % jrn_code))
                    inv_vals = {
                        'type': 'out_refund',
                        'journal_id': jrn_id.id,
                    }
                    invoice_id.update(inv_vals)
                    self.revert_sign_refund_invoice(invoice_id)
                # open invoice
                invoice_id.signal_workflow('invoice_open')
                self.recompute_number(invoice_id)
                # fix (insert) tax difference, in account move line
                taxes_ref = {
                    'tva': invoice_line_tax_tva.get('tax_tva'),
                    'te': invoice_line_tax_tva.get('tax_te')
                }
                self.fix_tax_difference(invoice_id, taxes_ref)
                # fin temporaire
                elp = timeit.default_timer() - st
                _logger.info('===  read %d / %s elapsed_time = %f ===' % (i+1, total, elp))
        return True

    @api.multi
    def clean_data_to_update(self, data):
        if not data:
            return data
        if float(data.get('interest_amount', 0)) == 0:
            data.pop('interest_amount')
        if float(data.get('tax_tva', 0)) == 0:
            data['tax_tva'] = '0'
        if float(data.get('tax_te', 0)) == 0:
            data['tax_te'] = '0'

    @api.multi
    def dispatch_mapped_data(self, data, kwargs):
        """
        :param: dict data:
        :param: dict kwargs:
        """
        if not data:
            return data
        #if data.get('interest_amount', False) in ('0', ''):
            #data.pop('interest_amount')
        tax_tva = data.get('tax_tva', '0')
        # _logger.info('\n=== data2 = %s === \n' % data)
        account_obj = self.env['account.account']
        el_req = [
            'partner_title', 'partner_customer',
            'partner_apporteur_a', 'partner_apporteur_b',
            'product', 'tax_te', 'tax_tva',
            'journal', 'account', 'invoice_line',
            'invoice', 'partner_ag', 'partner_sa',
        ]
        res = {}
        # res_partner_title
        res[el_req[0]] = {'name': data.get('title', False),
                          'shortcut': data.get('title', False)}
        # client_cour = [tdb_codeag,tdb_compte,tdb_titre,tdb_nom40,
        # tdb_datecomptable]
        # res_partner -> customer
        dfc = '0'
        if data.get('default_code')[0] == 'T':
            dfc = '1'
        elif data.get('default_code')[0] == 'M':
            dfc = '2'
        elif data.get('default_code')[0] == 'V':
            dfc = '3'
        else:
            raise exceptions.Warning(
                _('Error'), _('Not found <%s>' % data.get('default_code')[0]))
        ref_con = '41'
        if data.get('agency_id'):
            ref_con += data.get('agency_id') + '1'
        else:
            ref_con += '[NOAG]' + '1'
            raise exceptions.Warning(_('Error'), _('No agency'))
        if data.get('compte'):
            ref_con += data.get('compte')
        else:
            ref_con += '[NOCPT]'
            raise exceptions.Warning(_('Error'), _('No Compte'))

        res[el_req[1]] = {
            'name': data.get('name'),
            'customer': True,
            # 'ref': '41' + data.get('agency_id') + dfc + data.get('compte'),
            'ref': ref_con,
            'title': data.get('title', False),
        }
        # res_apporteur
        # Toujours vérifier les apporteurs même si codeag est dans code_gra et code_sa
        # code_all = code_sa + code_gra
        # if data.get('agency_id') not in code_all:
        agence_du_crt = data.get('agency_id')
        if agence_du_crt in code_sa:
            agence_du_crt = map_code_sa.get(agence_du_crt)
        if data.get('serial_identification_a') != '000':
            res[el_req[2]] = {
                'agency_id': agence_du_crt,
                'serial_identification': data.get('serial_identification_a'),
                'account_amount': float(data.get('code_app_a')),
            }
        if data.get('serial_identification_b') != '000':
            res[el_req[3]] = {
                'agency_id': agence_du_crt,
                'serial_identification': data.get('serial_identification_b'),
                'account_amount': float(data.get('code_app_b')),
            }
        # product_product
        res[el_req[4]] = {'default_code': data.get('default_code')}
        # common value
        price_unit = data.get('price_unit')
        access_amount = data.get('access_amount')
        tax_te = data.get('tax_te', '0')
        # _logger.info('\n=== tax_tva1 = %s === \n' % tax_tva)
        commag_amount = data.get('commag_amount')
        # Necessary value to compute TE rate
        res[el_req[5]] = {
            'price_unit': float(price_unit),
            'access_amount': float(access_amount),
            'tax_te': float(tax_te)
        }
        # Necessary value to compute TVA rate
        res[el_req[6]] = res[el_req[5]].copy()
        # _logger.info('\n=== tax_tva = %s === \n' % tax_tva)
        res[el_req[6]].update(tax_tva = float(tax_tva))
        """
        res[el_req[6]] = {
            'price_unit': float(price_unit),
            'access_amount': float(access_amount),
            'tax_te': float(tax_te)
            'tax_tva': float(tax_tva)
        }
        """
        res[el_req[7]] = {}
        res[el_req[8]] = {}
        # we have fixed that invoice should contain only two lines
        # check interav
        res[el_req[9]] = []
        if data.get('interest_amount', False):
            interest_amount = float(data.get('interest_amount'))
            interest_3 = {
                'product_id': 'INTERAV',
                'price_unit': float(interest_amount)
            }
            res[el_req[9]].append(interest_3)
            if interest_amount != 0.0:
                res[el_req[5]].update({'interest_amount': interest_amount})


        # check accessories product
        accessories = self.check_accessories(data.get('default_code'))
        product_1 = {'product_id': data.get('default_code'),
                     'price_unit': float(price_unit)}
        access_2 = {'product_id': accessories,
                    'price_unit': float(access_amount)}
        res[el_req[9]].append(product_1)
        if access_2.get('price_unit', 0.0) != 0.0:
            res[el_req[9]].append(access_2)
        elif access_2.get('price_unit', 0.0) == 0.0 and data.get('default_code')[:1] != 'V':
            res[el_req[9]].append(access_2)
        # Recherche de l'agence directe correspondant si agency_id est une sous agence
        agency_id = False
        agency_code = data.get('agency_id', False)
        if agency_code in code_sa:
            agency_direct_code = map_code_sa.get(agency_code)
            agency_id = self.env['base.agency'].search(
                [('code', '=', agency_direct_code)]).id
        else:
            agency_id = self.env['base.agency'].search(
                [('code', '=', data.get('agency_id'))]).id
        # TODO
        # compute domain of journal
        journal_doms = [('type', '=', 'sale'), ('agency_id', '=', agency_id)]
        categ_code = data.get('default_code')[:1]
        if categ_code in ['T', 'M']:
            journal_doms.append(('code', 'ilike', 'PN%'))
        else:
            journal_doms.append(('code', 'ilike', 'PV%'))
        journal_id = self.env['account.journal'].search(
            journal_doms, limit=1).id
        if not journal_id:
            # raise exceptions.Warning(_('Error'), _('No corresponding journal found'))
            journal_id = kwargs.get('journal_sale').id

        date_invoice = '01/' + data.get('period')
        date_invoice = datetime.strptime(date_invoice, '%d/%m/%Y')
        res[el_req[10]] = {
            'pol_numpol': data.get('pol_numpol'),
            'prm_datedeb': data.get('prm_datedeb'),
            'prm_datefin': data.get('prm_datefin'),
            'prm_numero_quittance': data.get('ordre'),
            'journal_id': journal_id,
            'account_id': kwargs.get('acc_410000').id,
            'comment': data.get('comment'),
            'date_invoice': date_invoice.date(),
        }
        # check if we have an General agent in this line
        # TODO
        if data.get('agency_id') in code_gra:
            # Agent Généraux
            res[el_req[11]] = {
                # 'agency_id': data.get('agency_id'),
                'agency_id': self.env['base.agency'].search([('code', '=', agency_code)], limit=1),
                'commag_amount': commag_amount,
            }
            # compte de facture different si agent généraux
            # res[el_req[10]]['account_id'] = self.env['account.account'].search([('code', '=', '411100')]).id
            res[el_req[10]]['account_id'] = kwargs.get('acc_411100').id
        elif data.get('agency_id') in code_sa:
            # sous agence
            res[el_req[12]] = {
                'agency_id': data.get('agency_id'),
                'account_amount': commag_amount,
                'serial_identification': '000',
                'is_under_agency': True,
            }

        return res

    @api.multi
    def archivate_incorrect_data(self, filename, fieldnames, row):
        """
        This function allow you to save all row contains bug.
        :params str filename: Content name of the file to be
        created or updated with his extension
        :params list fieldname: Content title of columns
        :params dict row: Content value to insert in csv file
        """
        if not fieldnames or not row:
            return False
        if not filename:
            filename = 'incorrect_data'
        path = '/opt/aro/filestore/' + filename
        if not os.path.isfile(path):
            with open(path, 'w') as csvfile:
                # fieldnames = ['first_name', 'las_name']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerow(row)
        else:
            with open(path, 'a') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writerow(row)

    #----------------------------------

    @api.multi
    def cru_partner_for_agency(self):
        try:
            agency_obj = self.env['base.agency']
            partner_obj = self.env['res.partner']

            # check agency with no partner
            agency_empty = agency_obj.search([('partner_id', '=', False)])
            for agency in agency_empty:
                partner_vals = {}
                if agency.code in code_gra:
                    partner_vals = {'name': agency.name, 'customer': True,
                                    'is_company': True}
                else:
                    partner_vals = {'name': agency.name, 'customer': False}
                new_partner = partner_obj.create(partner_vals)
                if new_partner:
                    agency.update({'partner_id': new_partner.id})

            # check agency with partner
            agency_full = agency_obj.search([('partner_id', '!=', False)])
            for agency in agency_full:
                partner_vals = {}
                if agency.code in code_gra:
                    partner_vals = {'name': agency.name, 'customer': True, 'is_company': True}
                else:
                    partner_vals = {'name': agency.name, 'customer': False}
                agency.partner_id.update(partner_vals)
        except Exception, e:
            raise e

    @api.multi
    def revert_sign_refund_invoice(self, invoices):
        if not invoices:
            return False
        if invoices.type == 'out_refund':
            for line in invoices.invoice_line:
                line_vals = {'price_unit': (-1) * line.price_unit}
                line.update(line_vals)
            invoices.button_reset_taxes()
            # for coms in invoices.commission_ids:
                # coms_vals = {'account_amount': (-1) * coms.account_amount}
                # coms.update(coms_vals)

    @api.multi
    def map_specified_data(self, data, map_to_use={}):
        """
        :param dict data:
        """
        if not data:
            return False
        if not map_to_use:
            return data
        buf = {}
        for elt in data:
            if map_to_use.get(elt):
                buf[map_to_use.get(elt)] = data.get(elt)
            else:
                buf[elt] = data.get(elt)
        return buf

    @api.multi
    def get_customer_account(self):
        account_obj = self.env['account.account']
        res = {
            'property_account_receivable': False,
            'property_account_payable': False,
        }
        res['property_account_receivable'] = account_obj.search([('code', '=', '410000')], limit=1)
        res['property_account_payable'] = account_obj.search([('code', '=', '463100')], limit=1)
        if res.get('property_account_receivable', False):
            res['property_account_receivable'] = res.get('property_account_receivable').id
        if res.get('property_account_payable', False):
            res['property_account_payable'] = res.get('property_account_payable', False).id
        return res


    @api.multi
    def check_accessories(self, data):
        if not data:
            return False
        code = data[:1]
        ref = 'ACC' + code
        return ref

    @api.multi
    def check_partner_title(self, data):
        opts = ['MR', 'MME', 'STE', 'PH', 'ST', 'BNQ', 'MAIS',
                'CBT', 'PROJ', 'MRMME', 'MAG', 'COOP', 'DEL',
                'ORG', 'MLLE', 'EGLIS', 'CEN', 'INC', 'ST?',
                'ECAR', 'UNI', 'ASSOC', 'ENT', 'CENTR',
                'AG', 'AMB', 'PROG', 'AMB', 'OFF', 'BUR',
                'ECOLE', 'ECOL', 'SARL', 'GROUP', 'CLB', 'ETB',
                'RES', 'HOT', 'CLG', '_', 'ETS', '00000']
        # title_obj = self.env['res.partner.title']
        res = False
        if data.get('shortcut') == opts[0]:
            res = self.env.ref('base.res_partner_title_sir')
        elif data.get('shortcut') == opts[1]:
            res = self.env.ref('base.res_partner_title_madam')
        elif data.get('shortcut') == opts[2]:
            res = self.env.ref('base.res_partner_title_pvt_ltd')
        else:
            return res
        return res

    @api.multi
    def check_partner_customer(self, data):
        if not data:
            return False
        res = False
        #account_obj = self.env['account.account']
        partner_obj = self.env['res.partner']
        # par = account_obj.search([('code', '=', '410000')], limit=1).ids
        # data['property_account_receivable'] = par[0] if par else False,
        # pap = account_obj.search([('code', '=', '463100')], limit=1).ids
        # data['property_account_payable'] = pap[0] if pap else False,
        if data.get('ref', False):
            data['title'] = self.check_partner_title({
                'name': data.get('title'), 'shortcut': data.get('title')})
            partner_src = partner_obj.search([('ref', '=', data.get('ref'))])
            if partner_src and len(partner_src) > 1:
                raise exceptions.Warning(_('Error'),
                                         _('More than one partner found with \
                                           ref %s' % data.get('ref')))
            elif partner_src and len(partner_src) == 1:
                if data.get('title', False):
                    data['title'] = data.get('title').id
                try:
                    partner_src.update(data)
                    res = partner_src
                except Exception, e:
                    raise exceptions.Warning(_('Error'), _('customer_data = %s\n warnning = %s' % (data, e)))
            elif not partner_src:
                # create new partner
                comp = self.env.ref('base.res_partner_title_pvt_ltd')
                if data.get('title'):
                    if data.get('title') == comp:
                        data['is_company'] = True
                    data['title'] = data.get('title').id
                res = partner_obj.create(data)
            else:
                # TODO
                # update partner before returning it
                return res
        else:
            raise exceptions.Warning(_('Error'), _('Can\'t create customer without ref'))
            return res
        return res

    @api.multi
    def check_partner_apporteur(self, data):
        if not data:
            return False
        res = False
        apporteur_obj = self.env['res.apporteur']
        agency_obj = self.env['base.agency']
        agency_id = data.get('agency_id', False)
        is_under_agency = data.get('is_under_agency', False)
        serial_id = data.get('serial_identification', False)
        agency_src = False
        apporteur_src = False
        apporteur_check = False
        ua_code = False
        # ==================================================
        # new style
        # ==================================================
        if data.get('account_amount', False):
            data.pop('account_amount')
        if is_under_agency:
            # sous agence
            # 1- recherche agence direct associé
            ua_code = agency_id
            agency_id = map_code_sa.get(agency_id)
            agency_src = agency_obj.search([('code', '=', agency_id)])
            if not agency_src:
                raise exceptions.Warning(_('Sorry !'),
                                         _('Agency with code <%s> doesn\'t exist yet' % agency_id))
            # mise à jour de data
            data['ua_code'] = ua_code
            data['agency_id'] = agency_src.id
            data['ref_apporteur'] = '41' + ua_code + '2000'
            # verification si sous agence existe déjà
            apporteur_check = apporteur_obj.search(
                [('ua_code', '=', ua_code),
                 ('agency_id', '=', agency_src.id)])
            if apporteur_check:
                apporteur_check.update(data)
            else:
                raise exceptions.Warning(_('Sorry !'),
                                         _('Under Agency with code <%s> was not found' % ua_code))
        else:
            # simple courtier
            # 1- recherche agence direct associé
            agency_src = agency_obj.search([('code', '=', agency_id)])
            if not agency_src:
                raise exceptions.Warning(_('Sorry !'),
                                         _('Agency with code <%s> doesn\'t exist yet' % agency_id))
            # mise à jour de data
            data['agency_id'] = agency_src.id
            data['ref_apporteur'] = '41' + agency_id + '2' + serial_id
            apporteur_check = apporteur_obj.search(
                [('serial_identification', '=', serial_id),
                 ('agency_id', '=', agency_src.id)], limit=1)
            if apporteur_check:
                # verifie le nom
                if apporteur_check.name.startswith('COURTIER') or apporteur_check.name.startswith('PARTENAIRE'):
                    data['name'] = 'PARTENAIRE ' + data.get('ref_apporteur')
                apporteur_check.update(data)
            else:
                # creation nouveau apporteur
                _logger.info('=== creation nouveau apporteur = %s ===' % data)
                # try to find all information about the new apporteur in tdc
                """
                sql_app = request_app + " where agence='%s' and old='%s'" \
                        % (agency_src.code, serial_id)
                cr_sql.execute(sql_app)
                """
                apps_mapped = self.env['tempdb.tdc'].search(
                    [('agence', '=', agency_src.code), ('old', '=', serial_id)], limit=1)
                # apps_mapped = self.map_cursor_content(cr_sql, map_app)
                map_buff = {}
                if apps_mapped:
                    map_buff.update({
                        'agency_id': apps_mapped.agence or False,
                        'serial_identification': apps_mapped.old or False,
                        'ap_code': apps_mapped.new or False,
                        'title': apps_mapped.titre or False,
                        'name': apps_mapped.name or False,
                        'statut': apps_mapped.statut or False
                    })
                # apps_mapped should contain only one dict or "nothing"
                """
                for app_mapped in apps_mapped:
                    for k, v in app_mapped.items():
                        map_buff[map_app[k]] = v
                """
                if map_buff:
                    # request_app = """select agence,old,new,titre,nom + ' ' + prenom name ,statut
                    # from tdc"""
                    title = map_buff.get('title', False)
                    if title:
                        map_buff['title'] = self.check_partner_title(
                            {'name': title.upper(),
                             'shortcut': title.upper()})
                    if map_buff.get('title', False):
                        map_buff['title'] = map_buff.get('title').id
                    else:
                        map_buff['title'] = False
                    agency_ref = map_buff.get('agency_id') if map_buff.get('agency_id') else agency_src.code
                    reference_apt = '41' + agency_ref + '2' + serial_id
                    map_buff['ref_apporteur'] = reference_apt
                    map_buff['agency_id'] = agency_obj.search(
                        [('code', '=', agency_ref)]).id
                else:
                    map_buff.update(data)
                    map_buff['title'] = False
                    map_buff['agency_id'] = agency_src.id
                    agency_ref = agency_src.code
                    reference_apt = '41' + agency_ref + '2' + serial_id
                    map_buff['ref_apporteur'] = reference_apt
                # check required field before creating apporteur
                if not map_buff.get('name', False):
                    map_buff['name'] = 'PARTENAIRE ' + map_buff.get('ref_apporteur')
                    #continue
                apporteur_check = apporteur_obj.create(map_buff)
        return apporteur_check
        # ==================================================

    @api.multi
    def check_product(self, data, from_inv_line=False):
        if not data:
            return False
        product_obj = self.env['product.product']
        product_src = False
        if not from_inv_line:
            product_src = product_obj.search(
                [('default_code', '=', data.get('default_code'))])
        else:
            product_src = product_obj.search(
                [('default_code', '=', data.get('product_id'))])
        if product_src:
            return product_src
        else:
            raise exceptions.Warning(_('Error'), _('No product found'))
            return False

    @api.multi
    def check_invoice(self, data):
        if not data:
            return False
        invoice_obj = self.env['account.invoice']
        # Add criteria to control invoice
        # comment is the ID of the record in sql server
        # so it should take all the line in the table
        doms = [
            ('pol_numpol', '=', data.get('pol_numpol')),
            ('comment', '=', data.get('comment'))]
        invoice_id = invoice_obj.search(doms)
        if invoice_id:
            invoice_id.update(data)
            return invoice_id
        else:
            return invoice_obj.create(data)

    @api.multi
    def check_invoice_line(self, data):
        if not data:
            return False
        line_obj = self.env['account.invoice.line']
        product_obj = self.env['product.product']
        doms = [('invoice_id', '=', data.get('invoice_id')),
                ('product_id', '=', data.get('product_id'))]
        line_src = line_obj.search(doms)
        if not line_src:
            product_obj = product_obj.browse(data.get('product_id'))
            data['account_id'] = product_obj.property_account_income.id
            data['name'] = product_obj.name if not product_obj.description else product_obj.description
            return line_obj.create(data)
        else:
            line_src.update(data)
            return line_src

    @api.multi
    def map_cursor_content(self, cursor_to_map, use_map={}):
        if not cursor_to_map:
            return False
        if not use_map:
            use_map = map_gnrl
        res = []
        columns = [column[0] for column in cursor_to_map.description]
        for row in cursor_to_map:
            col_counter = 0
            data = {}
            for col in columns:
                if type(row[col_counter]) == datetime.datetime:
                    data[col] = row[col_counter].strftime("%Y-%m-%d")
                elif type(row[col_counter]) == decimal.Decimal and col != 'comment':
                    data[col] = float(row[col_counter])
                elif type(row[col_counter]) == decimal.Decimal and col == 'comment':
                    data[col] = int(row[col_counter])
                elif type(row[col_counter]) == int:
                    data[col] = int(row[col_counter])
                elif type(row[col_counter]) == str:
                    data[col] = str(row[col_counter])
                else:
                    data[col] = row[col_counter]
                col_counter += 1
            res.append(data)
        return res

    @api.multi
    def check_nearest_tax(self, reference, value):
        """
        :param list reference: percentage (round,1)
        :param float value: percentage (round,1)
        :returned float res['value']: the rate
        :returned float res['difference']: the rate difference
        :returned char res['sign']: take 2 value:
            '+' -> upgrade the default rate (value)
            '-' -> downgrade the default rate (value)
        """
        te_list = [0.0, 3.0, 4.0, 4.5, 7.0, 14.5, 20.0]
        res = {}
        if not reference or not value:
            return res
        if value in reference:
            res['value'] = value
            return res
        for i, v in enumerate(reference):
            if value < v:
                res['value'] = reference[i - 1] if i != 0 else reference[i]
        return res

        #####################################
        #####################################
        """
        else:
            if value < 0.0:
                res['value'] = 0.0
                res['difference'] = value
                res['sign'] = '+'
            else:
                lf = 0.0
                rg = False
                # check left & right value
                for v in reference:
                    if value > v:
                        lf = v
                    if value < v:
                        rg = v
                        continue
                df_lf = value - lf
                df_rg = rg - value
                if df_lf == df_rg:
                    res['value'] = rg
                    res['difference'] = df_rg
                    res['sign'] = '+'
                elif df_lf > df_rg:
                    res['value'] = rg
                    res['difference'] = df_rg
                    res['sign'] = '+'
                else:
                    # elif df_lf < df_rg:
                    res['value'] = lf
                    res['difference'] = df_lf
                    res['sign'] = '-'
            return res
            """

    @api.multi
    def fix_tax_difference(self, invoice, taxes):
        """
        Insert difference between tax generated by odoo
        and tempdb in account move line
        :param record invoice: invoice that contain a move
        :param dict taxes: contain TVA and TE from tempdb
        """
        res = {}
        if not invoice:
            return res
        if not invoice.move_id:
            return res
        move_line = self.env['account.move.line']
        reverse_sgn = False
        ref = '/'
        if invoice.type in ('in_invoice', 'in_refund'):
            ref = invoice.reference
        else:
            ref = invoice.number
        if invoice.type == 'out_refund':
            reverse_sgn = True
        common_vals = {
            'partner_id': invoice.partner_id.id,
            'debit': 0.0, 'credit': 0.0,
            'name': 'Regul ecart', 'date': invoice.date_invoice,
            'ref': ref, 'quantity': 1.00,
            'product_id': False, 'product_uom_id': False,
            'move_id': invoice.move_id.id,
        }
        lines = []
        diff_total = 0.0
        for tax in invoice.tax_line:
            # check if invoice is out_refund
            tax_amount = tax.amount
            if reverse_sgn:
                tax_amount = -1 * tax.amount
            if tax.name.startswith('Tva') or tax.name.startswith('TVA'):
                diff_tva = round(tax_amount - taxes.get('tva'), 2)
                diff_total += diff_tva
                if diff_tva != 0.0:
                    line_tva = common_vals.copy()
                    line_tva['account_id'] = tax.account_id.id
                    line_tva['name'] = line_tva.get('name') + ' TVA'
                    if diff_tva > 0:
                        line_tva['debit'] = diff_tva
                    else:
                        line_tva['credit'] = abs(diff_tva)
                    lines.append(line_tva)
            elif tax.name.startswith('Te'):
                diff_te = round(tax_amount - taxes.get('te'), 2)
                diff_total += diff_te
                if diff_te != 0.0:
                    line_te = common_vals.copy()
                    line_te['account_id'] = tax.account_id.id
                    line_te['name'] = line_te.get('name') + ' TE'
                    if diff_te > 0:
                        line_te['debit'] = diff_te
                    else:
                        line_te['credit'] = abs(diff_te)
                    lines.append(line_te)
            else:
                raise exceptions.Warning(_('Error'), _('tax name %s doesn\'t start with <Tva> or <Te>' % tax.name))

        if diff_total != 0.0:
            # contre partie
            equilibrate = common_vals.copy()
            equilibrate['name'] = equilibrate.get('name') + ' Taxes'
            equilibrate['account_id'] = invoice.account_id.id
            if diff_total > 0:
                equilibrate['credit'] = diff_total
            else:
                equilibrate['debit'] = abs(diff_total)
            lines.append(equilibrate)

        for line in lines:
            ml_src = move_line.search([('move_id', '=', invoice.move_id.id), ('name', '=', line.get('name'))])
            if len(ml_src) > 1:
                raise exceptions.Warning(_('Error'), _('To much repeated line: %s' % ml_src.name))
            """
            if ml_src:
                try:
                    ml_src.unlink()
                except Exception, e:
                    raise Warning(
                        _('Error'),
                        _('Can\'t unlink %s -> %s \n \
                              %s' % (ml_src, ml_src.name, e)))
            """
            if not ml_src:
                try:
                    move_line.create(line)
                except Exception, e:
                    raise Warning(
                        _('Error'),
                        _('Can\'t insert value %s in account_move_line %s\n \
                              %s' % (str(line), line.get('name'), e)))

        invoice.move_id.post()
        invoice._log_event()
        return res

    @api.multi
    def get_rate_te(self, data):
        # res should be contain the ID of <Register Taxe>
        # possible value for te:
        # TODO
        # convert res to dict
        te_list = [0.0, 3.0, 4.0, 4.5, 7.0, 14.5, 20.0]
        res = False
        tax_obj = self.env['account.tax']
        tax_te = data.get('tax_te', 0.0)
        pn = data.get('price_unit')
        acs = data.get('access_amount')
        interav = data.get('interest_amount', 0.0)
        te_rate = 0.0
        if tax_te != 0.0:
            if pn + acs != 0.0:
                te_rate = abs((tax_te/(pn + acs))) * 100
            elif interav != 0.0:
                te_rate = abs((tax_te/(interav))) * 100
            else:
                te_rate = 0.0
                # return res
        te_rate = round(te_rate, 1)
        if te_rate not in te_list:
            te_rate = min(enumerate(te_list), key=lambda x: abs(x[1] - te_rate))
            te_rate = round(te_rate[1], 1)
        # decommente les lignes en dessous pour toujours avoir un TE
        # te_rate_near = self.check_nearest_tax(te_list, te_rate)
        # te_rate = te_rate_near.get('value')
        #if te_rate_near.get('difference', False):
            # res['difference'] = te_rate_near.get('difference')
            # res['sign'] = te_rate_near.get('sign')
        code = 'Te-' + str(te_rate)
        doms = [('description', '=', code)]
        res = tax_obj.search(doms)
        return res

    @api.multi
    def get_rate_tva(self, data):
        # res should be contain the ID of <Legal Taxe>
        res = {}
        tva_list = [0.0, 20.0]
        tax_obj = self.env['account.tax']
        tax_te = data.get('tax_te')
        tax_tva = data.get('tax_tva', 0.0)
        pn = data.get('price_unit')
        acs = data.get('access_amount')
        tva_rate = 0.0
        if tax_tva != 0.0:
            if pn + acs + tax_te != 0.0:
                tva_rate = abs(tax_tva/(pn + acs + tax_te)) * 100
            else:
                return res
        if abs(tva_rate) == 0.0:
            tva_rate = 0.0
        res['tva_code'] = tva_rate
        tva_rate = round(tva_rate, 1)
        if tva_rate not in tva_list:
            tva_rate = min(enumerate(tva_list), key=lambda x: abs(x[1] - tva_rate))
            tva_rate = round(tva_rate[1], 1)
        #min(enumerate(a), key=lambda x: abs(x[1] - tva_rate))
        # decommente la ligne en dessous pour toujours avoir un TVA
        # tva_rate_near = self.check_nearest_tax(tva_list, tva_rate)
        # tva_rate = tva_rate_near.get('value')
        #if tva_rate_near.get('difference', False):
            # res['difference'] = tva_rate_near.get('difference')
            # res['sign'] = tva_rate_near.get('sign')
        code = 'Tva-' + str(tva_rate)
        doms = [('description', '=', code)]
        tva_id = tax_obj.search(doms)
        if tva_id:
            res['tva_id'] = tva_id
        return res

    @api.multi
    def track_corresponding_tva(self, te_rate, tva_rate):
        res = {}
        if not tva_rate:
            return res
        rt = [0.045, 0.145, 0.07, 0.03, 0.04, 0.2, 0.0]
        tax_obj = self.env['account.tax']
        if tva_rate.description != 'Tva-0.0':
            if te_rate.amount == rt[0]:
                code = 'Tva-20.9'
                res['tax_id'] = tax_obj.search([('description', '=', code)])
            elif te_rate.amount == rt[1]:
                code = 'Tva-22.9'
                res['tax_id'] = tax_obj.search([('description', '=', code)])
            elif te_rate.amount == rt[2]:
                code = 'Tva-21.4'
                res['tax_id'] = tax_obj.search([('description', '=', code)])
            elif te_rate.amount == rt[3]:
                code = 'Tva-20.6'
                res['tax_id'] = tax_obj.search([('description', '=', code)])
            elif te_rate.amount == rt[4]:
                code = 'Tva-20.8'
                res['tax_id'] = tax_obj.search([('description', '=', code)])
            elif te_rate.amount == rt[5]:
                code = 'Tva-24.0'
                res['tax_id'] = tax_obj.search([('description', '=', code)])
            elif te_rate.amount == rt[6]:
                code = 'Tva-20.0'
                res['tax_id'] = tax_obj.search([('description', '=', code)])
            else:
                res['tva_amount'] = tva_rate
                res['te_amount'] = te_rate
                # res = False
        elif tva_rate.description == 'Tva-0.0':
            code = 'Tva-0.0'
            res['tax_id'] = tax_obj.search([('description', '=', code)])
        else:
            res['tva_amount'] = tva_rate
            res['te_amount'] = te_rate
            # res = False
        return res

    @api.multi
    def check_commission_apporteur(self, data):
        if not data:
            return False
        res = False
        commission_obj = self.env['commission.commission']
        # may i can skip this search to win time
        res = commission_obj.search(
            [('partner_commissioned', '=', data.get('partner_commissioned')),
             ('commission_invoice', '=', data.get('commission_invoice'))])
        if res:
            res.update(data)
            return res
        else:
            return commission_obj.create(data)

    @api.multi
    def check_account_apporteur(self, app_type='CRT', product_categ='T'):
        """
        :param app_type: can take 3 values:
            CRT -> simple Courtier
            GRA -> General Agent
            UAG -> Under Agency
        :param product_categ can take 3 values:
            T -> Terrestre
            M -> Maritime
            V -> Vie
        """
        res = {}
        account_obj = self.env['account.account']
        if app_type == 'CRT':
            crt_charge = {'charge_T': '642053', 'charge_M': '642054', 'charge_V': '641052'}
            crt_cpt = {'compte': '411200'}
            res['account_commission'] = account_obj.search([('code', '=', crt_cpt.get('compte'))]).id
            if product_categ == 'T':
                res['account_charge_commission'] = account_obj.search([('code', '=', crt_charge.get('charge_T'))]).id
            elif product_categ == 'M':
                res['account_charge_commission'] = account_obj.search([('code', '=', crt_charge.get('charge_M'))]).id
            elif product_categ == 'V':
                res['account_charge_commission'] = account_obj.search([('code', '=', crt_charge.get('charge_V'))]).id
            else:
                res['account_charge_commission'] = False

        elif app_type == 'GRA':
            gra_charge = {'charge_T': '642051', 'charge_M': '642052', 'charge_V': '641051'}
            gra_cpt = {'compte': '411100'}
            res['account_commission'] = account_obj.search([('code', '=', gra_cpt.get('compte'))]).id
            if product_categ == 'T':
                res['account_charge_commission'] = account_obj.search([('code', '=', gra_charge.get('charge_T'))]).id
            elif product_categ == 'M':
                res['account_charge_commission'] = account_obj.search([('code', '=', gra_charge.get('charge_M'))]).id
            elif product_categ == 'V':
                res['account_charge_commission'] = account_obj.search([('code', '=', gra_charge.get('charge_V'))]).id
            else:
                res['account_charge_commission'] = False
        elif app_type == 'UAG':
            uag_charge = {'charge_T': '642053', 'charge_M': '642054', 'charge_V': '641052'}
            uag_cpt = {'compte': '411200'}
            res['account_commission'] = account_obj.search([('code', '=', uag_cpt.get('compte'))]).id
            if product_categ == 'T':
                res['account_charge_commission'] = account_obj.search([('code', '=', uag_charge.get('charge_T'))]).id
            elif product_categ == 'M':
                res['account_charge_commission'] = account_obj.search([('code', '=', uag_charge.get('charge_M'))]).id
            elif product_categ == 'V':
                res['account_charge_commission'] = account_obj.search([('code', '=', uag_charge.get('charge_V'))]).id
            else:
                res['account_charge_commission'] = False
        else:
            return res
        return res

    @api.multi
    def recompute_number(self, invoice):
        if not invoice:
            return False

        int_num = invoice.internal_number
        in_list = int_num.split('/')
        in_list[1] = '2015'
        in_list = '/'.join(in_list)
        invoice.write({'internal_number': in_list, 'number': in_list})
        # invoice_id.action_number()
        if invoice.type in ('in_invoice', 'in_refund'):
            if not invoice.reference:
                ref = invoice.number
            else:
                ref = invoice.reference
        else:
            ref = invoice.number

        self._cr.execute(""" UPDATE account_move SET ref=%s, name=%s
                       WHERE id=%s""",
                    (ref, ref, invoice.move_id.id))
        self._cr.execute(""" UPDATE account_move_line SET ref=%s
                       WHERE move_id=%s""",
                    (ref, invoice.move_id.id))
        self._cr.execute(""" UPDATE account_analytic_line SET ref=%s
                       FROM account_move_line
                       WHERE account_move_line.move_id = %s AND
                             account_analytic_line.move_id = account_move_line.id""",
                    (ref, invoice.move_id.id))
        invoice.invalidate_cache()

        return True

    @api.model
    def update_add_record(self):
        #self.cru_partner_for_agency()
        # delete log for each_execution
        path_log = '/opt/aro/filestore/tempdb.csv'
        try:
            os.remove(path_log)
        except Exception, e:
            _logger.info('\n=== Exception = %s === \n' % e)
        mapped_datas = self.map_cursor_content(cursorSQLServer)
        cust_acc = self.get_customer_account()
        com_list = []
        fieldnames = []
        dpt_datas_all = []
        invoice_all = self.env['account.invoice']
        agency_obj = self.env['base.agency']
        apt_obj = self.env['res.apporteur']
        compteur = len(mapped_datas)
        for mob_counter, mapped_data in enumerate(mapped_datas):
            to_log = mapped_data.copy()
            _logger.info('=== %s / %s comment = %s ===' % (mob_counter + 1, compteur, mapped_data.get('comment')))
            #com_list = []
            # ================================================
            # init fieldname to use in incorrect_data log
            # ================================================
            if not fieldnames:
                fieldnames.append('bugs')
                for k, v in mapped_data.iteritems():
                    fieldnames.append(k)
            # ================================================
            # Test data before mapping
            # ================================================
            md_codeag = mapped_data.get('CODEAG', False)
            # check if not in sous agence
            if md_codeag not in code_sa:
                ag_src = agency_obj.search([('code', '=', md_codeag)])
                if not ag_src:
                    # archivate_incorrect_data(self, filename, fieldnames, row)
                    to_log['bugs'] = 'agence %s not found' % md_codeag
                    self.archivate_incorrect_data('tempdb.csv', fieldnames, to_log)
                    _logger.info('=== Next ===')
                    continue
            # ================================================
            # start mapping
            # ================================================
            #invoice_vals = {'partner_id': False, }
            mapped_data = self.map_specified_data(mapped_data, map_sql2)
            #dpt_datas = self.dispatch_mapped_data(mapped_data)
            dpt_datas_all.append(self.dispatch_mapped_data(mapped_data))

        del mapped_datas
        self.invalidate_cache()
        ttx = len(dpt_datas_all)
        tto = 0
        for dpt_datas in dpt_datas_all:
            big_st = timeit.default_timer()
            tto += 1
            #_logger.info('=== %s / %s ===' % (tto, ttx))
            com_list = []
            invoice_vals = {'partner_id': False, }
            px_ctg = dpt_datas.get('product').get('default_code')[:1]
            # ================================================
            # Check invoice
            # ================================================
            invoice_vals.update(dpt_datas.get('invoice'))
            # Check res_partner_title
            # partner_title = self.check_partner_title(dpt_datas.get('partner_title'))
            # ================================================
            # Check the right partner to use in invoice
            # ================================================
            # Check if customer exist
            part_cust = dpt_datas.get('partner_customer')
            self.patch_partner(cursorSQLServer, dpt_datas, cust_acc, part_cust, com_list, invoice_vals, px_ctg)
            # _logger.info('=== com_list = %s ===' % com_list)
            if invoice_vals.get('partner_id', False):
                invoice_vals['partner_id'] = invoice_vals.get('partner_id', False).id
            if invoice_vals.get('final_customer_id', False):
                invoice_vals['final_customer_id'] = invoice_vals.get('final_customer_id', False).id
            invoice_id = self.check_invoice(invoice_vals)
            # ================================================
            # si des commission ont été défini avant la creation de la facture
            # alors mettre à jour le champ commission_invoice avec l'id de cette dernière
            # ================================================
            com_buf_list = []
            for com in com_list:
                if not com.get('commission_invoice', False):
                    com['commission_invoice'] = invoice_id.id
                com_buf_list.append(com)
            com_list = []
            com_list = com_buf_list
            # ================================================
            # Check apporteur
            # ================================================
            # TODO
            appa_id = False
            appa_dict = dpt_datas.get('partner_apporteur_a', False)
            if appa_dict:
                appa_dict_a = appa_dict.copy()
                appa_dict_a.pop('account_amount')
                appa_id = self.check_partner_apporteur(cursorSQLServer, appa_dict_a)
            appb_id = False
            appb_dict = dpt_datas.get('partner_apporteur_b', False)
            if appb_dict:
                appb_dict_b = appb_dict.copy()
                appb_dict_b.pop('account_amount')
                appb_id = self.check_partner_apporteur(cursorSQLServer, appb_dict_b)
            # ================================================
            # Check account for commission line
            # ================================================
            # TODO
            # replace fixed value 'CRT' by computed value
            # to check it if it's <CRT> or <GRA>
            if appa_id:
                com_acca = self.check_account_apporteur('CRT', px_ctg)
                account_amount_a = appa_dict.get('account_amount', 0.0)
                com_list.append({
                    'partner_commissioned': appa_id.partner_id.id,
                    'account_amount': account_amount_a,
                    'account_commission': com_acca.get('account_commission', False),
                    'account_charge_commission': com_acca.get('account_charge_commission', False),
                    'commission_invoice': invoice_id.id})
                # app_list.append(appa_id.id)
            if appb_id:
                com_accb = self.check_account_apporteur('CRT', px_ctg)
                account_amount_b = appb_dict.get('account_amount', 0.0)
                com_list.append({
                    'partner_commissioned': appb_id.partner_id.id,
                    'account_amount': account_amount_b,
                    'account_commission': com_accb.get('account_commission', False),
                    'account_charge_commission': com_accb.get('account_charge_commission', False),
                    'commission_invoice': invoice_id.id})
            # _logger.info('=== com_list final = %s ===' % com_list)
            self.check_commission_apporteur_all(com_list)
            # =======================================================
            # Prepare invoice_line taxes
            # =======================================================
            # invoice_line_tax_id = {}
            taxes_list = []
            # Treatment of TE Rate
            invoice_line_tax_te = dpt_datas.get('tax_te')
            rate_te = self.get_rate_te(invoice_line_tax_te)
            if rate_te:
                taxes_list.append(rate_te.id)
            else:
                # insert in log
                to_log['bugs'] = 'TE rate not found'
                self.archivate_incorrect_data('tempdb.csv', fieldnames, to_log)
                _logger.info('=== Next TE rate===')
                continue
            # Treatment of TVA Rate
            invoice_line_tax_tva = dpt_datas.get('tax_tva')
            rate_tva = self.get_rate_tva(invoice_line_tax_tva)
            if not rate_tva.get('tva_id', False):
                # insert in log
                _logger.info('=== TVA rate not found ===')
                to_log['bugs'] = 'TVA rate <%s> not found' % rate_tva.get('tva_code', '?')
                self.archivate_incorrect_data('tempdb.csv', fieldnames, to_log)
                _logger.info('=== Next TVA rate===')
                continue
            rate_tva = self.track_corresponding_tva(rate_te, rate_tva.get('tva_id', False))
            if rate_tva.get('tax_id', False):
                taxes_list.append(rate_tva.get('tax_id').id)
            else:
                # insert in log
                _logger.info('===bug rate_tva = %s ===' % rate_tva)
                to_log['bugs'] = 'Corresponding TVA <%s / %s> rate not found' % (rate_tva.get('te_amount'), rate_tva.get('tva_amount'))
                self.archivate_incorrect_data('tempdb.csv', fieldnames, to_log)
                _logger.info('=== Next Corresponding TVA rate===')
                continue

            invoice_line_tax_id = [(6, 0, taxes_list)]
            # =======================================================
            # Prepare invoice_line data
            # =======================================================
            invoice_lines = dpt_datas.get('invoice_line')
            self.patch_invoice_lines(invoice_lines, invoice_id, rate_te, invoice_line_tax_id)
            # recompute_taxe
            invoice_id.button_reset_taxes()
            # invoice_all += invoice_id
            # _logger.info('=== invoice_all = %s ===' % invoice_all)
            total_time = timeit.default_timer() - big_st
            _logger.info('=== line  %s /%s in %f sec ===' % (tto, ttx, total_time))

            # reset type of invoice if amount_total < 0
            put_to_out_refund = False
            if invoice_id.amount_total < 0:
                put_to_out_refund = True
            elif invoice_id.amount_total == 0:
                for com_id in invoice_id.commission_ids:
                    if com_id.account_amount < 0 and put_to_out_refund is not True:
                        _logger.debug('=== put to out_refund ===')
                        put_to_out_refund = True

            if put_to_out_refund:
                _logger.info('=== reset type invoice and account ===')
                journal_id = invoice_id.journal_id
                jrn_code = journal_id.code
                if jrn_code.startswith('P'):
                    jrn_code = 'V' + jrn_code[1:]
                jrn_id = self.env['account.journal'].search([('code', '=', jrn_code)])
                if not jrn_id:
                    raise exceptions.Warning(_('Error'), _('Journal with code <%s> doesn\'t exist' % jrn_code))
                inv_vals = {
                    'type': 'out_refund',
                    'journal_id': jrn_id.id,
                }
                invoice_id.update(inv_vals)
                self.revert_sign_refund_invoice(invoice_id)
            # open invoice
            invoice_id.signal_workflow('invoice_open')
            self.recompute_number(invoice_id)
            # fix (insert) tax difference, in account move line
            taxes_ref = {
                'tva': invoice_line_tax_tva.get('tax_tva'),
                'te': invoice_line_tax_tva.get('tax_te')
            }
            self.fix_tax_difference(invoice_id, taxes_ref)
            # ttct += 1
            # inv_time = timeit.default_timer() - inv_st
            # _logger.info('=== invoice %s /%s in %f sec ===' % (ttct , ttl, inv_time))
        connection.close()
        _logger.info('\n=== Close connection ===\n')

    @api.multi
    def patch_partner(self, dpt_datas, cust_acc, part_cust, com_list, invoice_vals, px_ctg):
        if dpt_datas.get('partner_ag', False):
            # _logger.info('=== p_ag===')
            p_ag = dpt_datas.get('partner_ag')
            agency_code = p_ag.get('agency_id')
            # agency_code = agency_obj.search([('code', '=', agency_code)], limit=1)
            # verification account_ag
            if agency_code:
                com_gra = self.check_account_apporteur('GRA', px_ctg)
                account_amount_gra = p_ag.get('commag_amount', 0.0)
                vals_ag = {
                    'partner_commissioned': agency_code.partner_id.id,
                    'account_amount': account_amount_gra,
                    'account_commission': com_gra.get('account_commission', False),
                    'account_charge_commission': com_gra.get('account_charge_commission', False),
                    'commission_invoice': False,
                    }
                com_list.append(vals_ag)
            invoice_vals['partner_id'] = agency_code.partner_id
            # part_cust = dpt_datas.get('partner_customer')
            part_cust.update(cust_acc)
            invoice_vals['final_customer_id'] = self.check_partner_customer(part_cust)
        elif dpt_datas.get('partner_sa', False):
            # _logger.info('=== p_sa===')
            apt_dict = dpt_datas.get('partner_sa', {})
            agency_code = apt_dict.get('agency_id')
            # TODO manque critère
            # apt_src = apt_obj.search([('ua_code', '=', agency_code)], limit=1)
            vals = apt_dict.copy()
            vals.pop('account_amount')
            apt_id = self.check_partner_apporteur(vals)
            # verification account_apporteur
            if apt_id:
                com_apt = self.check_account_apporteur('UAG', px_ctg)
                account_amount_sa = apt_dict.get('account_amount', 0.0)
                com_list.append(
                    {'partner_commissioned': apt_id.partner_id.id,
                     'account_amount': account_amount_sa,
                     'account_commission': com_apt.get('account_commission', False),
                     'account_charge_commission': com_apt.get('account_charge_commission', False),
                     'commission_invoice': False})
            # part_cust = dpt_datas.get('partner_customer')
            part_cust.update(cust_acc)
            invoice_vals['partner_id'] = self.check_partner_customer(part_cust)
            invoice_vals['final_customer_id'] = invoice_vals.get('partner_id', False)
        else:
            # part_cust = dpt_datas.get('partner_customer')
            part_cust.update(cust_acc)
            invoice_vals['partner_id'] = self.check_partner_customer(part_cust)
            invoice_vals['final_customer_id'] = invoice_vals.get('partner_id', False)

    @api.multi
    def check_commission_apporteur_all(self, com_list):
        for cl in com_list:
            self.check_commission_apporteur(cl)

    @api.multi
    def patch_invoice_lines(self, invoice_lines, invoice_id, rate_te, invoice_line_tax_id):
        for invoice_line in invoice_lines:
            # Check product
            # product_id = self.check_product(dpt_datas.get('product'))
            product_id = self.check_product(invoice_line, True)
            if product_id:
                invoice_line['product_id'] = product_id.id
            if invoice_id:
                invoice_line['invoice_id'] = invoice_id.id
            # insert taxes in invoice_line data
            if product_id.default_code != 'INTERAV':
                invoice_line['invoice_line_tax_id'] = invoice_line_tax_id
            else:
                invoice_line['invoice_line_tax_id'] = [(6, 0, [rate_te.id])]
            self.check_invoice_line(invoice_line)
