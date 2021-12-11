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
    visi = fields.Boolean("Visible web",default=True)


class ResConfigSettingsCustom(models.TransientModel):
    _inherit = 'res.config.settings'

    terms_and_conditions = fields.Text(string='Terminos y Condiciones', default="")

    @api.model
    def get_values(self):
        res = super(ResConfigSettingsCustom, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update({
            'terms_and_conditions': str(params.get_param('terms_and_conditions')) or ""
        })
        return res

    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param('terms_and_conditions', self.terms_and_conditions)
        super(ResConfigSettingsCustom, self).set_values()


class ProductTemplateCustom(models.Model):
    _inherit = 'product.template'

    terms_and_conditions = fields.Text(string='Terminos y Condiciones de sitio web', compute='get_term_and_conditions')

    def get_term_and_conditions(self):
        params = self.env['ir.config_parameter'].sudo()
        terms = params.get_param('terms_and_conditions')
        for rec in self:
            rec.terms_and_conditions = terms


