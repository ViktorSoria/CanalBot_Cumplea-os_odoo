# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
import datetime
import calendar
import logging

_log = logging.getLogger("stock_picking (%s) -------> " % __name__)


class ResPartnerCustom(models.Model):
    _inherit = "res.partner"

    phone = fields.Char(required=True)

