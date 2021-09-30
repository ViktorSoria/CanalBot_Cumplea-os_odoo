# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
import datetime
import calendar
import logging

_log = logging.getLogger("pos_order (%s) -------> " % __name__)


class Pos_PaymentCustom(models.Model):
    _inherit = "pos.payment"

    seller = fields.Many2one('res.users', string="Vendedor", related='pos_order_id.user_id')



