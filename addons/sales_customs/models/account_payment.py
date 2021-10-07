# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
import datetime
import calendar
import logging

_log = logging.getLogger("account_payment (%s) -------> " % __name__)


class AccountPaymentCustom(models.Model):
    _inherit = "account.payment"

    seller_original = fields.Many2one('res.users', string="Vendedor en Factura", compute='get_seller_from_invoice')

    def get_seller_from_invoice(self):
        for rec in self:
            rec.seller_original = rec.reconciled_invoice_ids[0].invoice_user_id if rec.reconciled_invoice_ids else None




