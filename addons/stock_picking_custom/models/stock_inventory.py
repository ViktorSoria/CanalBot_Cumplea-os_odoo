# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
import datetime
import calendar
import logging

_log = logging.getLogger("stock_inventory (%s) -------> " % __name__)


class StockInventoryCustom(models.Model):
    _inherit = "stock.inventory"


    category_products_PDV = fields.Many2many('pos.category', relation='model_act', string="Categoria PDV")

    @api.onchange('category_products_PDV')
    def _calc_products(self):
        #Agrega productos
        products = self.env['product.product'].search([('pos_categ_id', 'in', self.category_products_PDV.ids), ('id', 'not in', self.product_ids.ids)])
        self.write({'product_ids': [(6, 0, products.ids)]})


class StockMoveCustom(models.Model):
    _inherit = "stock.move"

    def calc_productqty(self):

        squant = self.env['stock.quant'].search([('location_id', '=', self.location_id.id),
                                                 ('product_id', '=', self.product_id.id)])
        # _log.info("Está calculando cual es el stock actual:::  %s qty: %s " % (squant, squant.quantity))

        act_qty = squant.quantity
        # act_qty = squant.available_quantity

        return act_qty


class StockQuantWizard(models.TransientModel):
    _name = "wizard.download.data"

    # locations =
    # stock_quants_ids =

    def download_data(self):
        _log.info('Button')

