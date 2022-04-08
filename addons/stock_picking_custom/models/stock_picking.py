# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
import datetime
import calendar
import logging
from odoo.exceptions import UserError

_log = logging.getLogger("stock_picking (%s) -------> " % __name__)


class StockPickingCustom(models.Model):
    _inherit = "stock.picking"

    who_recibe = fields.Char(string="Quien entrega")

    seller = fields.Many2one('res.users', string="Vendedor", compute='compute_seller_team', store=True)
    team_sale = fields.Many2one('crm.team', string="Equipo de Ventas", compute='compute_seller_team', store=True)
    packager = fields.Char(string="Empacador")

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

    @api.onchange("picking_type_id")
    def confirmTransfer(self):
        self.is_transfer = self.picking_type_id._es_transferencia

    def _get_origin_destiny(self):
        origen = None
        destino = None
        doc_orig = None
        if not self.origin:
            origen = self.location_id.complete_name
            destino = self.location_transfer_id.complete_name

        else:
            doc_orig = self.search([('name','=',self.origin)])
            origen = doc_orig.location_id.complete_name
            destino = doc_orig.location_transfer_id.complete_name

        return [origen,destino,doc_orig]

    is_transfer = fields.Boolean("Es Transferencia entre Sucursales")
    location_transfer_id = fields.Many2one('stock.location', string="Ubicación de destino")

    @api.constrains('location_id','location_dest_id')
    def _check_different_origin_destiny(self):
        if self.location_id.id==self.location_dest_id.id or self.location_id.id==self.location_transfer_id.id:
            raise UserError(_("El lugar de destino no debe ser igual al de origen"))

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


class StockPickingOperationTypes(models.Model):
    _inherit="stock.picking.type"

    _es_transferencia = fields.Boolean("Es transferencia entre sucursales ")
