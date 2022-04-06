

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