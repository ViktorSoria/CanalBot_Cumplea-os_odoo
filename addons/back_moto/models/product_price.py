

from odoo import fields, models, api
from odoo.exceptions import UserError
import xlrd
import tempfile
import csv
from io import StringIO
import base64
import logging

_logger = logging.getLogger("Moto Control")


class ProductTemplate(models.Model):
    _inherit = "product.template"

    line_ids = fields.Many2many("product.price.transient",string="Precios",compute="compute_line_price")

    def compute_line_price(self):
        products = [(product,False,False) for product in self]
        data = self.env['product.pricelist']._compute_price_rule_multi(products)
        tarifas = self.env['product.pricelist'].search_read(fields=['id', 'name'])
        tarifas = {d['id']:d['name'] for d in tarifas}
        for p in self:
            prices = [{'name':"Precio del Producto",'precio':self.list_price,"product_id": p.id}]
            data_p = data[p.id]
            for tarifa,precio in data_p.items():
                prices.append({
                    'name': tarifas[tarifa],
                    "precio": precio[0],
                    "item_id": precio[1],
                    "list_price_id": tarifa,
                    "product_id": p.id,
                })
            lines = self.env['product.price.transient'].create(prices)
            p.line_ids = [(6,0,lines.ids)]


class ProducPrice(models.TransientModel):
    _name = "product.price.transient"

    name = fields.Char("Descripción")
    precio = fields.Float("Precio")
    item_id = fields.Many2one("product.pricelist.item","Item")
    list_price_id = fields.Many2one("product.pricelist","Lista")
    product_id = fields.Many2one("product.template")

    def change_price(self):
        if self.item_id and self.item_id.product_tmpl_id.id == self.product_id.id:
            self.item_id.write({'compute_price':'fixed','fixed_price':self.precio})
        elif self.list_price_id:
            self.list_price_id.write({'item_ids':[(0,0,{'compute_price':'fixed','fixed_price':self.precio,'applied_on':'1_product','product_tmpl_id':self.product_id.id})]})
        else:
            self.product_id.write({'list_price':self.precio})

    def edit_line(self):
        return {
            'name': "Editar Precio",
            'type': "ir.actions.act_window",
            'res_model': "product.price.transient",
            'res_id': self.id,
            'view_mode': "form",
            'view_type': "form",
            'target': "new",
        }