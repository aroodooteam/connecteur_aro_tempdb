# -*- coding: utf-8 -*-

from openerp import models, fields


class CsvMapSetting(models.Model):
    _name = 'csv.map.setting'
    _description = 'map data in csv file'

    csv_col = fields.Char(string='Csv Column', help='Name of column in csv')
    pgm_fld = fields.Char(string='Odoo field', help='Name of field in domain')
    used_in_domain = fields.Boolean(string='Domain criteria',
                                    help='Will be use to check if data exist')
    cbm_id = fields.Many2one('csv.base.model', string='Base Model')
