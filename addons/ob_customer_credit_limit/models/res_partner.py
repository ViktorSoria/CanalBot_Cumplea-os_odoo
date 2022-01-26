# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_log = logging.getLogger("%s ======>>>" % __name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    credit_check = fields.Boolean('Activar Credito', help='Activar limite de credito para clientes')
    credit_warning = fields.Monetary('Monto de advertencia')
    credit_blocking = fields.Monetary('Monto de Bloqueo')
    amount_due = fields.Monetary('Due Amount', compute='_compute_amount_due')
    credit_real = fields.Monetary('Total por cobrar', help="El total de lo facturado menos el total de pagos válidos.")

    def _compute_credit_real(self):
        # _log.info("Trigger works fine! ")
        payment_ids = self.env['account.payment'].search([('partner_id', '=', self.id), ('state', '=like', "posted")])
        total_payments = sum(payment_ids.mapped('amount'))
        # _log.info("_______ TOTAL PAGOS: %s " % total_payments)
        invoice_ids_all = self.env['account.move'].search([('partner_id', '=', self.id),
                                                       ('state', '=like', "posted")])
        inv_out = invoice_ids_all.filtered(lambda inv: inv.move_type in ['out_invoice'])
        total_invoices = sum(inv_out.mapped('amount_total'))
        notas_credito = invoice_ids_all.filtered(lambda inv: inv.move_type in ['out_refund'])
        total_notas = sum(notas_credito.mapped('amount_total'))
        # _log.info("_______ TOTAL FACTURADO: %s Total de facturas: %s" % (total_invoices, len(invoice_ids)))
        self.credit_real = total_invoices-total_payments-total_notas

    @api.depends('credit', 'debit')
    def _compute_amount_due(self):
        for rec in self:
            rec._compute_credit_real()
            # _log.info("________ DEBIT::: %s " % rec.debit)
            rec.amount_due = rec.credit_real - rec.debit

    @api.constrains('credit_warning', 'credit_blocking')
    def _check_credit_amount(self):
        for credit in self:
            if credit.credit_warning > credit.credit_blocking:
                raise ValidationError(_('Warning amount should not be greater than blocking amount.'))
            if credit.credit_warning < 0 or credit.credit_blocking < 0:
                raise ValidationError(_('Warning amount or blocking amount should not be less than zero.'))
