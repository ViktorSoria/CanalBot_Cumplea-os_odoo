

from odoo import fields, models, api
import logging

_logger = logging.getLogger("Pos Control")


class User(models.Model):
    _inherit = "product.pricelist"

    autorizacion = fields.Boolean("Require autorizacion")
    visible = fields.Boolean("Visible en el punto de venta")