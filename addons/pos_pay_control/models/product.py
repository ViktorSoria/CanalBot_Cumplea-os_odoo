

from odoo import fields, models, api
from datetime import timedelta
import logging

_logger = logging.getLogger("Pos negado")


class ProductoNegado(models.Model):
    _name = "product.product.negado"

    name = fields.Many2one("product.product","Producto")
    cantidad = fields.Integer("Cantidad Negada")
    pos_id = fields.Many2one("pos.config","Sucursal")
    location_id = fields.Many2one("stock.location","Almacen",related="pos_id.picking_type_id.default_location_src_id", store=True)

    @api.model
    def create_line(self,product_id,cantidad,pos_id):
        data = {'name':product_id,
                'cantidad':cantidad,
                'pos_id':pos_id}
        _logger.warning(data)
        try:
            self.create(data)
        except:
            return False
        return True


class Product(models.Model):
    _inherit = "product.product"

    @api.model
    def validate_stock(self,productos,location):
        p = {a[0]:a[1] for a in productos}
        read_prod = self.env['product.product'].with_context(location=location).search_read(domain=[('id', 'in', list(p.keys()))], fields=['qty_available'])
        stock_falt = [[r['id'],r['qty_available']] for r in read_prod if p[r['id']] > r['qty_available']]
        return stock_falt or False