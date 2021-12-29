from odoo import models, fields


class EditarPrecioUnitario(models.Model):
    _inherit = "sale.order.line"

    def PermisoPrecioUnitario(self):
        self.cambiar_precio_unitario = self.env['res.users'].has_group('website_prueba.group_edit_unit_price')

    cambiar_precio_unitario = fields.Boolean(string='Modificar precio unitario', compute='PermisoPrecioUnitario',default=False)
