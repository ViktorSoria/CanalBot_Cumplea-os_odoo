# -*- coding: utf-8 -*-

from odoo import models
import logging
from odoo.exceptions import UserError


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
        delete_lines = []
        for line in self.order_line:
            quant_id = all_stock_quant.filtered(lambda sq: sq.product_id.id == line.product_id.id and sq.package_id==False)
            if quant_id.available_quantity <= 0:
                delete_lines.append(line.id)
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
        if len(delete_lines) > 0:
            # _log.info("Borrando las lineas:: %s" % delete_lines)
            self.order_line = [(2, line_id) for line_id in delete_lines]
        if not self.order_line or len(self.order_line.ids) <= 0:
            raise UserError("No es posible confirmar un pedido sin lineas de pedido o sin stock en todas sus lineas")
        res = super(SaleOrderCust, self).action_confirm()
        return res
