# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
import datetime
import calendar
import logging

_log = logging.getLogger("stock_quant_package (%s) -------> " % __name__)


class StockQuantPackageCustom(models.Model):
    _inherit = "stock.quant.package"

    def get_empacador_name(self):
        picking_line_ids = self.env['stock.move.line'].search([('result_package_id', '=', self.id)], limit=1)[:1]
        if not picking_line_ids:
            return "Sin fecha de confirmación"
        picking_id = picking_line_ids.picking_id
        return str(picking_id.packager)

    def get_picking_validate_date(self):
        picking_line_ids = self.env['stock.move.line'].search([('result_package_id', '=', self.id)], limit=1)[:1]
        if not picking_line_ids:
            return "Sin fecha de confirmación"
        picking_id = picking_line_ids.picking_id
        return str(picking_id.date_done.date())

