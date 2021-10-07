# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
import datetime
import calendar
import logging

_log = logging.getLogger("account_payment (%s) -------> " % __name__)


class AccountPaymentCustom(models.Model):
    _inherit = "account.payment"

    seller_original = fields.Many2one('res.users', string="Vendedor", compute='get_seller_from_invoice')

    def get_seller_from_invoice(self):
        self.seller_original = self.reconciled_invoice_ids[0].invoice_user_id if self.reconciled_invoices_count else None




