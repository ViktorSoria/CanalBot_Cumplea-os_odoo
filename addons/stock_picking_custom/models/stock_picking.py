# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
import datetime
import calendar
import logging

_log = logging.getLogger("stock_picking (%s) -------> " % __name__)


class StockPickingCustom(models.Model):
    _inherit = "stock.picking"

    who_recibe = fields.Char(string="Quien entrega")

    seller = fields.Many2one('res.users', string="Vendedor", compute='compute_seller_team', store=True)
    team_sale = fields.Many2one('crm.team', string="Equipo de Ventas", compute='compute_seller_team', store=True)

    @api.depends('picking_type_id')
    def compute_seller_team(self):
        # _log.warning("Entre depends")
        for record in self:
            if record.picking_type_id and record.picking_type_code == 'outgoing':
                if record.sale_id:
                    record.seller = record.sale_id.user_id
                    record.team_sale = record.sale_id.user_id.sale_team_id
                    continue
                elif record.pos_order_id:
                    record.seller = record.pos_order_id.user_id
                    record.team_sale = record.pos_order_id.user_id.sale_team_id
                    continue
            # _log.warning(record.seller)
            # _log.warning(record.team_sale)
            record.seller = None
            record.team_sale = None

    is_transfer = fields.Boolean("Es Transferencia entre Sucursales")
    location_transfer_id = fields.Many2one('stock.location', string="Ubicación de destino")

    @api.onchange('location_transfer_id')
    def _change_location_dest(self):
        self.location_dest_id = self.location_transfer_id.virtual_location

    @api.onchange('is_transfer')
    def _change_location_false(self):
        self.location_dest_id = False
        self.location_transfer_id = False


class StockLocationCustom(models.Model):
    _inherit = "stock.location"

    virtual_location = fields.Many2one('stock.location', string="Ubicación Virtual")

