# -*- coding: utf-8 -*-

from odoo import api, models, fields, _

import logging

_log = logging.getLogger("__--__-->> ws products: %s" % __name__)


# class WsProductTemplate(models.Model):
#     _inherit = "product.template"
#
#     product_cat_line_ids = fields.Many2many('ws.product.line', 'product_tmpl_ids', string="Lineas de producto")


class WsProductPublicCategory(models.Model):
    _inherit = "product.public.category"

    ws_product_line_ids = fields.Many2many('ws.product.line', 'product_catg_public_id', string="Lineas asociadas")


class WsProductLine(models.Model):
    _name = "ws.product.line"
    _description = "Lineas de productos (para categorizar)"
    _sql_constraints = [
        ('name_constrain', 'unique(name)', 'No pueden existir dos lineas de productos con el mismo nombre.'),
    ]

    name = fields.Char(string="Nombre de linea", required=True)
    # product_tmpl_ids = fields.Many2many("product.template", "product_cat_line_ids", string="Productos de ésta linea")
    product_catg_public_id = fields.Many2many('product.public.category', string="Categoria de sitio web")

