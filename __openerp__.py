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
###############################################################################
{
    'name': 'Connecteur V9 - ARO Tempdb',
    'version': '1.0',
    'category': 'ARO',
    'description': """
Used to connect V9-Odoo Application
===========================================
**Credits:** Haritiana M. Rakotoamalala.
""",
    'depends': ['base'],
    'website': 'http://www.aro.mg',
    'author': 'Haritiana Maminiaina Rakotomalala <haryoran04@gmail.com>',
    'data': [
        'security/ir.model.access.csv',
        'data/connecteur.xml',
        'data/move_line_data.xml',
        'data/move_line_2016.xml',
        'views/csv_loader_views.xml',
        'views/csv_base_model_views.xml',
        'views/tempdb_tdc_views.xml',
        'views/connecteur_csv_views.xml',
        'data/tempdb.tdc.csv',
        'data/connecteur_csv_data.xml',
    ],
    'demo': [],
    'auto_install': False,
    'installable': True,
}
