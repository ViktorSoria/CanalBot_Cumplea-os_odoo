# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
import datetime
import calendar
import logging

_log = logging.getLogger("stock_picking (%s) -------> " % __name__)


class StockPickingCustom(models.Model):
    _inherit = "stock.picking"

    who_recibe = fields.Char(string="Quien recibe")

    code_picking = fields.Selection(related='picking_type_id.code')
    seller = fields.Many2one('res.users', string="Vendedor", compute='_compute_seller_team')
    team_sale = fields.Many2one('crm.team', string="Equipo de Ventas", compute='_compute_seller_team')

    def _compute_seller_team(self):
        for record in self:
            if not record.picking_type_id and record.picking_type_id.code != 'outgoing':
                record.seller = None
                record.team_sale = None
                return
            if record.sale_id:
                order = record.sale_id
            elif record.pos_order_id:
                order = record.pos_order_id
            else:
                record.seller = None
                record.team_sale = None
                return
            record.seller = order.user_id
            record.team_sale = record.seller.sale_team_id
