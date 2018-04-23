# -*- coding: utf-8 -*-

from openerp import models, fields, api
import logging
_logger = logging.getLogger(__name__)


class CsvBaseModel(models.Model):
    _name = 'csv.base.model'
    _description = 'Specify model will be used'
    _order = 'sequence'

    name = fields.Many2one('ir.model', string='Model', required=True)
    model = fields.Char(related='name.model', string='Model name',
                        readonly=True)
    sequence = fields.Integer(string='Sequence', default=1,
                              help='Order of model to check')
    mapset_ids = fields.One2many('csv.map.setting', 'cbm_id',
                                 string='Map Setting')
    allow_create = fields.Boolean(string='Create',
                                  help='Create data if not exist')
    allow_update = fields.Boolean(string='Update',
                                  help='Update data if exist')
    domain_mapping = fields.Char(string='Domain')
    csv_loader_id = fields.Many2one('csv.loader', string='Csv Loader')
    output_field = fields.Char(string='Out field', help='Name of field to map')

    @api.multi
    def compute_domain(self, line):
        if not self.mapset_ids:
            return []
        domain = []
        for mapset in self.mapset_ids:
            if mapset.used_in_domain:
                domain.append((str(mapset.pgm_fld), '=',
                               line.get(str(mapset.csv_col), False)))
            self.update_line(mapset, line)
        return domain

    @api.multi
    def update_line(self, mapset, line):
        line[mapset.map_fld] = line.pop(mapset.csv_col)
        return line

    @api.multi
    def check_create_or_update(self, model_obj, line):
        if model_obj and self.allow_update is True:
            _logger.info('\n=== update ===\n')
        if not model_obj and self.allow_create is True:
            _logger.info('\n=== create ===\n')
