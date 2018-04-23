# -*- coding: utf-8 -*-

from openerp import models, fields


class TempdbTdc(models.Model):
    _name = 'tempdb.tdc'
    _description = 'Load tempdb_tdc in recup nom apporteur'

    name = fields.Char(string='Name')
    statut = fields.Char(string='Statut')
    agence = fields.Char(string='Agence', size=4)
    old = fields.Char(string='Old', size=8)
    new = fields.Char(string='New', size=16)
    titre = fields.Char(string='Titre', size=16)
