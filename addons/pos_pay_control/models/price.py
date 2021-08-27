

from odoo import fields, models, api
from datetime import timedelta
import logging

_logger = logging.getLogger("Pos Control")


class User(models.Model):
    _inherit = "product.pricelist"

    autorizacion = fields.Boolean("Require autorizacion")


class Discount(models.Model):
    _name = "price.discount"

    name = fields.Char("Nombre")
    descrip = fields.Text("Descripcion")
    desc = fields.Selection([('por','Procentaje'),('fijo','Fijo')],default="por",string="Tipo de descueto")
    value = fields.Float("Valor")
    categ_ids = fields.Many2many("pos.category",'category_discount_rel','discount_id','category_id',"Categorias")
    product_ids = fields.Many2many("product.product",'product_discount_rel','discount_id','product_id',"Productos")
    pos_ids = fields.Many2many("pos.config",'config_discount_rel','discount_id','config_id',"Puntos de venta")
    active = fields.Boolean("Activo",default=True)
    start_date = fields.Date("Fecha de Inicio")
    end_date = fields.Date("Fecha de Fin")
    start_hour = fields.Float("Hora de Inicio")
    end_hour = fields.Float("Hora de Fin")
    day_ids = fields.Many2many("day.week",'dias_discount_rel','discount_id','product_id',"Dias")
    etiqueta_ids = fields.Many2many("res.partner.category",'eti_discount_rel','discount_id','etiqueta_id',"Etiquetas")
    fil_cliente = fields.Boolean("Filtrar clientes")

    def archive_applicant(self):
        self.write({'active':False})

    def get_discount(self,product_id,cliente_id,pos):
        data = {'desc':False,'value':0}
        options = self.env['price.discount'].search([])
        options = options.filter_pos(pos)
        options = options.filter_fecha()
        options = options.filter_cliente(cliente_id)
        options = options.filter_producto(product_id)
        if options:
            data['desc'] = options[0].desc
            data['value'] = options[0].value
        return data

    def filter_pos(self,pos):
        return self.filtered(lambda l: pos in l.pos_ids.ids)

    def filter_fecha(self):
        date = fields.Datetime.now() - timedelta(hours=5)
        options = self.env['price.discount']
        for rec in self:
            if rec.start_date and rec.start_date > date.date():
                continue
            if rec.end_date and rec.end_date < date.date():
                continue
            if date.weekday() not in rec.day_ids.mapped('value'):
                continue
            if rec.start_hour and rec.start_hour > date.hour + date.minute/60:
                continue
            if rec.end_hour and rec.end_hour < date.hour + date.minute/60:
                continue
            options += rec
        return options

    def filter_cliente(self,cliente_id):
        options = self.env['price.discount']
        eti = self.env['res.partner'].browse(cliente_id).category_id
        for rec in self:
            if rec.fil_cliente:
                if rec.etiqueta_ids & eti:
                    options += rec
            else:
                options += rec
        return options

    def filter_producto(self,product_id):
        options = self.env['price.discount']
        product = self.env['product.product'].browse(product_id)
        category = product.pos_categ_id
        for rec in self:
            if product_id in rec.product_ids.ids:
                options += rec
            else:
                cat_ids = self.env['pos.category'].search([('id', 'child_of', rec.categ_ids.ids)])
                if category in cat_ids:
                    options += rec
        return options


class Day(models.Model):
    _name = "day.week"

    name = fields.Char("Nombre")
    value = fields.Integer("Valor")