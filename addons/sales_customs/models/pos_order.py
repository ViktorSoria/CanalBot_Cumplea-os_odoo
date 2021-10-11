# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
import datetime
import calendar
import logging

_log = logging.getLogger("pos_order (%s) -------> " % __name__)


class Pos_PaymentCustom(models.Model):
    _inherit = "pos.payment"

    seller = fields.Many2one('res.users', string="Vendedor")

    @api.model
    def create(self, vals):
        if 'pos_order_id' in vals:
            seller = self.env['pos.order'].browse(vals['pos_order_id']).user_id
            if seller:
                vals['seller'] = seller.id
        return super(Pos_PaymentCustom, self).create(vals)

    def get_seller_from_order(self):
        for rec in self:
            rec.seller = rec.pos_order_id.user_id if rec.pos_order_id else None
