# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
import datetime
import calendar
import logging

_log = logging.getLogger("stock_quant_package (%s) -------> " % __name__)


class StockQuantPackageCustom(models.Model):
    _inherit = "stock.quant.package"

    def get_picking_data(self):
        picking_line_ids = self.env['stock.move.line'].search([('result_package_id', '=', self.id)], limit=1)[:1]
        if not picking_line_ids:
            return False
        picking_id = picking_line_ids.picking_id
        return {
            'date_done': str(picking_id.date_done.date()),
            'packager': str(picking_id.packager),
            'client': str(picking_id.partner_id.name),
            'origin': str(picking_id.origin)
        }

