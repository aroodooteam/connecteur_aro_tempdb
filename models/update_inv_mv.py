# -*- coding: utf-8 -*-

from openerp import api, models
import logging
import timeit
logger = logging.getLogger(__name__)

MAX_LIMIT = 950000
class UpdateInvMv(models.Model):
    _name = 'update.inv.mv'
    _description = 'Update invoice number and move reference with police, quittance, effect date'

    @api.multi
    def get_invoice_to_update_by_number(self, number):
        inv_obj = self.env['account.invoice']
        # search invoice to update
        inv_ids = inv_obj.search([('number', 'ilike', number)], limit=MAX_LIMIT)
        logger.info('inv_ids = %s' % len(inv_ids))
        return inv_ids

    @api.multi
    def get_invoice_to_update(self, year, month='01'):
        # init model object
        inv_obj = self.env['account.invoice']
        period_obj = self.env['account.period']

        # search period_id
        code = month + '/' + str(year)
        # period_ids = period_obj.search([('code', 'like', code)])
        period_ids = period_obj.search([('code', 'ilike', '%/2016')])

        # search invoice to update
        inv_ids = inv_obj.search([('period_id', 'in', period_ids.ids), '|', ('number', 'ilike', '%/2015/%'), ('number', 'ilike', '%/2017/%')], limit=MAX_LIMIT)
        logger.info('inv_ids = %s' % len(inv_ids))
        return inv_ids

    @api.multi
    def get_ir_cron(self):
        cron_obj = self.env['ir.cron']
        cron_id = cron_obj.search([('name', '=', 'Update invoice and move')])
        return cron_id

    @api.model
    def update_reference_by_number(self):
        """
        update reference start from invoice
        """
        year = 2016
        number = 'PN/2016/%'
        aroriaka = 'PN93'
        invoice_ids = self.get_invoice_to_update_by_number(number)
        jrnl_obj = self.env['account.journal']
        jrnl_id = jrnl_obj.search([('code', '=', aroriaka)])
        i = 0
        inv_total = len(invoice_ids)
        for inv in invoice_ids:
            big_st = timeit.default_timer()
            i += 1
            sequence = self.env['ir.sequence'].next_by_id(jrnl_id.sequence_id.id)
            # sequence = inv.journal_id.sequence_id.next_by_id()
            # logger.info('old_seq = %s / new_sequence = %s' % (inv.number,sequence))
            number = sequence.split('/')
            number = jrnl_id.code + '/' + str(year) + '/' + number[2]
            logger.info('old_seq = %s / new_sequence = %s' % (sequence, number))
            vals = {
                'number': number,
                'journal_id': jrnl_id.id
            }
            inv.write(vals)

            # update move field
            vals_mv = {
                'name': inv.number,
                'ref': inv.number,
                'num_police': inv.pol_numpol,
                'num_quittance': inv.prm_numero_quittance,
                'date_effect': inv.prm_datedeb,
                'date_end': inv.prm_datefin,
                'journal_id': inv.journal_id.id,
            }
            inv.move_id.write(vals_mv)

            rqt = """
            update account_move_line set emp_police = '%s', emp_quittance = '%s', emp_effet = '%s', emp_datech = '%s', emp_datfact = '%s', journal_id = %s, ref = '%s' where move_id = %s
            """ % (inv.pol_numpol, inv.prm_numero_quittance, inv.prm_datedeb, inv.prm_datefin, inv.date_invoice, inv.journal_id.id, inv.number, inv.move_id.id)
            # logger.info('\n=== rqt = %s === \n' % rqt)
            self._cr.execute(rqt)
            logger.info('[%s] %s / %s in %s sec' % (inv.move_id.id, i, inv_total, round(timeit.default_timer() - big_st, 2)))

    @api.model
    def update_reference(self):
        """
        update reference start from invoice
        """
        year = 2016
        month = '09'
        invoice_ids = self.get_invoice_to_update(year, month)
        if invoice_ids:
            i = 0
            inv_total = len(invoice_ids)
            for inv in invoice_ids:
                big_st = timeit.default_timer()
                i += 1
                number = inv.number.split('/')
                number = number[0] + '/' + str(year) + '/' + number[2]
                # logger.info('%s (%s = %s)' % (inv.id, inv.number, number))
                # update invoice number
                inv.write({'number': number})

                # update move field
                vals_mv = {
                    'name': inv.number,
                    'ref': inv.number,
                    'num_police': inv.pol_numpol,
                    'num_quittance': inv.prm_numero_quittance,
                    'date_effect': inv.prm_datedeb,
                    'date_end': inv.prm_datefin
                }
                inv.move_id.write(vals_mv)

                # update move_line
                # vals_mv_line = {
                #     'emp_police': inv.pol_numpol,
                #     'emp_quittance': inv.prm_numero_quittance,
                #     'emp_effet': inv.prm_datedeb,
                #     'emp_datech': inv.prm_datefin,
                #     'emp_datfact': inv.date_invoice,
                # }
                # inv.move_id.line_id.write(vals_mv_line)
                rqt = """
                update account_move_line set emp_police = '%s', emp_quittance = '%s', emp_effet = '%s', emp_datech = '%s', emp_datfact = '%s' where move_id = %s
                """ % (inv.pol_numpol, inv.prm_numero_quittance, inv.prm_datedeb, inv.prm_datefin, inv.date_invoice, inv.move_id.id)
                # logger.info('\n=== rqt = %s === \n' % rqt)
                self._cr.execute(rqt)
                # for mv_line in inv.move_id.line_id:
                #     logger.info('move_line_id = %s' % mv_line.id)
                #     mv_line.update(vals_mv_line)
                logger.info('[%s] %s / %s in %s sec' % (inv.move_id.id, i, inv_total, round(timeit.default_timer() - big_st, 2)))
            # logger.info('mv_ids = %s' % invoice_ids.mapped('move_id'))
            # logger.info('mvl_ids = %s' % invoice_ids.mapped('move_id.line_id'))
            """
            mvl_ids = invoice_ids.mapped('move_id.line_id')
            total = len(mvl_ids)
            c = 0
            for mvl_id in mvl_ids:
                big_stl = timeit.default_timer()
                vals_mv_line = {
                    'emp_police': mvl_id.move_id.num_police,
                    'emp_quittance': mvl_id.move_id.num_quittance,
                    'emp_effet': mvl_id.move_id.date_effect,
                    'emp_datech': mvl_id.move_id.date_end,
                    'emp_datfact': mvl_id.move_id.date,
                }
                mvl_id.update(vals_mv_line)
                c += 1
                logger.info('[%s] %s / %s in %s sec' % (mvl_id.id, c, total, round(timeit.default_timer() - big_stl, 2)))
            """
            # self.update_reference()
        return True

    @api.multi
    def update_from_move_line(self):
        period_obj = self.env['account.period']
        period_dom = [('code', 'ilike', '%/2016')]
        period = period_obj.search(period_dom)
        move_line_obj = self.env['account.move.line']
        # production PN and PV
        # move_line_ids = move_line_obj.search([('emp_police', '=', False), ('period_id', 'in', period.ids), '|', ('ref', 'ilike', 'PN%'), ('ref', 'ilike', 'PV%')])
        # avoir VN and VV
        move_line_ids = move_line_obj.search([('emp_police', '=', False), ('period_id', 'in', period.ids), '|', ('ref', 'ilike', 'VN%'), ('ref', 'ilike', 'VV%')])
        logger.info('=== len(move_line_ids) = %s ===' % len(move_line_ids))
        invoice = move_line_ids.mapped('invoice')
        logger.info('=== len(invoice) = %s ===' % len(invoice))
        return invoice

    @api.model
    def update_move_line(self):
        """
        CARE ! Ref is supposed to be correct in this function
        """
        invoice_ids = self.update_from_move_line()
        inv_total = len(invoice_ids)
        i = 0
        for inv in invoice_ids:
            big_st = timeit.default_timer()
            i += 1
            # update move
            vals_mv = {
                'num_police': inv.pol_numpol,
                'num_quittance': inv.prm_numero_quittance,
                'date_effect': inv.prm_datedeb,
                'date_end': inv.prm_datefin
            }
            inv.move_id.write(vals_mv)

            # update move_line
            # vals_mv_line = {
            #     'emp_police': inv.pol_numpol,
            #     'emp_quittance': inv.prm_numero_quittance,
            #     'emp_effet': inv.prm_datedeb,
            #     'emp_datech': inv.prm_datefin,
            #     'emp_datfact': inv.date_invoice,
            # }
            # inv.move_id.line_id.write(vals_mv_line)
            rqt = """
            update account_move_line set emp_police = '%s', emp_quittance = '%s', emp_effet = '%s', emp_datech = '%s', emp_datfact = '%s' where move_id = %s
            """ % (inv.pol_numpol, inv.prm_numero_quittance, inv.prm_datedeb, inv.prm_datefin, inv.date_invoice, inv.move_id.id)
            # logger.info('\n=== rqt = %s === \n' % rqt)
            self._cr.execute(rqt)
            logger.info('[%s] %s / %s in %s sec' % (inv.move_id.id, i, inv_total, round(timeit.default_timer() - big_st, 2)))
