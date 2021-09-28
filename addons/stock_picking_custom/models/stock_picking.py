# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
import datetime
import calendar
import logging

_log = logging.getLogger("stock_picking (%s) -------> " % __name__)


class StockPickingCustom(models.Model):
    _inherit = "stock.picking"

    who_recibe = fields.Char(string="Quien recibe")

