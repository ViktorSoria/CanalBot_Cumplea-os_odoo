# -*- coding: utf-8 -*-

from odoo import models
import logging

_log = logging.getLogger("sale_order (%s) -------> " % __name__)


class SaleOrderCust(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):

        # Al validar una orden de venta,
        # el sistema filtre automáticamente lo que hay a mano,
        # si no hay a mano cree automáticamente un pedido o cotización con una referencia BK.

        # ---------------------

        # Si no hay suficiente para vender entonces que les venta lo que tiene y lo que falte se los ponga en otro presupuesto pero con la referencia BK.

        _log.info("CONFIRMANDO... SEGÚN")
        all_products = self.order_line.mapped('product_id')
        sq_domain = [
            ('product_id', 'in', all_products.ids),
            ('location_id', '=', self.warehouse_id.lot_stock_id.id)
        ]
        all_stock_quant = self.env['stock.quant'].search(sq_domain)
        bk_lines = []
        for line in self.order_line:
            quant_id = all_stock_quant.filtered(lambda sq: sq.product_id.id == line.product_id.id)
            if quant_id.available_quantity < line.product_uom_qty:
                # Create new line.
                bk_line = (0, 0, {
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.product_uom_qty - quant_id.available_quantity,
                    'product_uom': line.product_uom.id,
                    'price_unit': line.price_unit
                })
                bk_lines.append(bk_line)
                # Affect current line (less if needed)
                line.product_uom_qty = quant_id.available_quantity
        if len(bk_lines) > 0:
            bk_order = self.env['sale.order'].create({
                'name': "BK_"+self.name,
                'partner_id': self.partner_id.id,
                'pricelist_id': self.pricelist_id.id,
                'order_line': bk_lines
            })
        res = super(SaleOrderCust, self).action_confirm()
        return res