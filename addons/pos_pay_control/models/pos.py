

from odoo import fields, models, api
import json
import logging

_logger = logging.getLogger("Pos Control")


class Order(models.Model):
    _inherit = "pos.order"

    def write(self,vals):
        res = super(Order,self).write(vals)
        if vals.get('state','') == 'paid':
            self.acomula_puntos()
        return res

    def acomula_puntos(self):
        partner = self.partner_id
        acomulados = 0
        usado = 0
        for l in self.payment_ids:
            if l.payment_method_id.es_puntos:
                usado += l.amount
            else:
                acomulados += l.amount
        puntos = acomulados * 0.04 - usado
        partner.write({'puntos':partner.puntos+ puntos})


class Pospaymentm(models.Model):
    _inherit = "pos.payment.method"

    cargo = fields.Float("Cargo porcentual")
    es_puntos = fields.Boolean("Es Puntos electronicos")


class Posconfig(models.Model):
    _inherit = "pos.config"

    producto_cargo = fields.Many2one('product.product',"Producto Cargo")
    datos_ubicacion = fields.Char("Datos ubicacion",compute="get_datos")

    def get_datos(self):
        for rec in self:
            partner_id = rec.picking_type_id.warehouse_id.partner_id
            nombre = partner_id.name  #calle numero colonia cp ciudad estado
            direccion = "{} #{} Col. {} {} {}, {}".format(partner_id.street_name or '',
                                                               partner_id.street_number or 'SN',
                                                               partner_id.l10n_mx_edi_colony or '',
                                                               ('C.P. '+partner_id.zip) if partner_id.zip else '',
                                                               partner_id.city_id.name or partner_id.city or '',
                                                               partner_id.state_id.name or ''
                                                       )
            telefono = "Tel: "+partner_id.phone
            rec.datos_ubicacion = '/'.join([nombre,direccion,telefono])


class PosSession(models.Model):
    _inherit = "pos.session"

    orders = fields.One2many("pos.order.temp","session_id","Pedidds")

    def envia(self,data):
        try:
            data = json.loads(data)
            data['session'] = self.name
            data['unpaid_orders'][0]['pos_session_id'] = self.id
            data['unpaid_orders'][0]['user_id'] = self.user_id.id
            self.env['pos.order.temp'].create({'session_id':self.id,'json':json.dumps(data)})
        except Exception as e:
            _logger.warning(e)
            return False
        return True

    def recibe(self):
        data = self.orders.mapped('json')
        #self.orders.unlink()
        return data


class PosOrderTemp(models.TransientModel):
    _name = "pos.order.temp"

    session_id = fields.Many2one("pos.session","Sesion")
    json = fields.Text("Json")