

from odoo import fields, models, api
import logging

_logger = logging.getLogger("Pos Control")


class Partner(models.Model):
    _inherit = "res.partner"

    acomula_puntos = fields.Boolean("Acomula puntos")
    puntos = fields.Float("Puntos")
    no_editable = fields.Boolean("No editable")

    def write(self,vals):
        if vals.get('acomula_puntos'):
            if not self.no_editable:
                vals['no_editable'] = True
        return super(Partner,self).write(vals)


class User(models.Model):
    _inherit = "res.users"

    user_pay = fields.Boolean("Pago de pedidos")
    clave = fields.Integer("Clave adminitracion")

    def autorize(self,code):
        code = int(code) if code else 0
        aut = self.env['res.users'].search([('clave','=',code),('clave','!=',False),('clave','!=',0)],limit=1)
        return True if aut else False