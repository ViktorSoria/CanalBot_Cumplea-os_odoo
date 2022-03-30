

from odoo import fields, models, api
from datetime import datetime, timedelta
import json
import werkzeug.urls
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

    def get_cfdi_vals(self):
        try:
            o = self.account_move
            vals = {}
            cfdi_vals = o._l10n_mx_edi_decode_cfdi()
            vals['sello'] = cfdi_vals.get('sello')
            vals['sello_sat'] = cfdi_vals.get('sello_sat')
            vals['cadena'] = cfdi_vals.get('cadena')
            vals['certificate_number'] = cfdi_vals.get('certificate_number')
            vals['certificate_sat_number'] = cfdi_vals.get('certificate_sat_number')
            vals['expedition'] = cfdi_vals.get('expedition')
            vals['fiscal_regime'] = cfdi_vals.get('fiscal_regime')
            vals['emission_date_str'] = cfdi_vals.get('emission_date_str')
            vals['stamp_date'] = cfdi_vals.get('stamp_date')
            vals['uuid'] = cfdi_vals.get('uuid')

            vals['sello_cor'] = vals['sello'][-8:]
            vals['decimal_places'] = o.currency_id.decimal_places
            vals['l10n_mx_edi_cfdi_supplier_rfc'] = o.l10n_mx_edi_cfdi_supplier_rfc
            vals['l10n_mx_edi_cfdi_customer_rfc'] = o.l10n_mx_edi_cfdi_customer_rfc
            vals['l10n_mx_edi_cfdi_amount'] = '%.*f' % (o.currency_id.decimal_places, o.l10n_mx_edi_cfdi_amount)
            qr_vals = werkzeug.urls.url_quote_plus('https://verificacfdi.facturaelectronica.sat.gob.mx/default.aspx?'+
                                're='+vals['l10n_mx_edi_cfdi_supplier_rfc']+ '&rr='+vals['l10n_mx_edi_cfdi_customer_rfc']+
                                '&tt='+vals['l10n_mx_edi_cfdi_amount']+ '&id='+vals['uuid']
                                + '&fe='+vals['sello_cor'])
            vals['qr'] = '/report/barcode/?type=QR&value=%s&width=180&height=180'%qr_vals
            return json.dumps(vals)
        except:
            return False

    @api.model
    def recibev2(self):
        domain = [['state', '=', 'paid']]
        model = 'pos.order'
        fields = ['display_name', 'name', 'config_id']
        res = self.env[model].search_read(domain=domain, fields=fields)
        return res


class Pospaymentm(models.Model):
    _inherit = "pos.payment.method"

    cargo = fields.Float("Cargo porcentual")
    es_puntos = fields.Boolean("Es Puntos electronicos")

    def name_get(self):
        result = []
        for s in self:
            name = s.name + (' +{}%'.format(s.cargo) if s.cargo >0 else '')
            result.append((s.id, name))
        return result


class Posconfig(models.Model):
    _inherit = "pos.config"

    producto_cargo = fields.Many2one('product.product',"Producto Cargo")
    datos_ubicacion = fields.Char("Datos ubicacion",compute="get_datos")
    default_client = fields.Many2one("res.partner", string="Cliente por default")
    es_caja = fields.Boolean("Es caja")

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
            telefono = "Tel: "+(partner_id.phone or '')
            rec.datos_ubicacion = '/'.join([nombre,direccion,telefono])


class PosSession(models.Model):
    _inherit = "pos.session"

    orders = fields.One2many("pos.order.temp","session_id","Pedidds")

    def envia(self, data):
        try:
            data = json.loads(data)
            data['session'] = self.name
            data['unpaid_orders'][0]['pos_session_id'] = self.id
            data['unpaid_orders'][0]['user_id'] = self.user_id.id
            dic = {
                'session_id': self.id,
                'json': json.dumps(data),
                'orden': data['unpaid_orders'][0]['name'],
                'cajero': self.env['hr.employee'].browse(data['unpaid_orders'][0]['employee_id']).name if data['unpaid_orders'][0]['employee_id'] else "",
                'pos_name': self.config_id.display_name
            }
            self.env['pos.order.temp'].create(dic)
        except Exception as e:
            _logger.warning(e)
            return False
        return True

    def ver(self):
        pos_order = self.env['pos.order'].search([('pos_reference','in',self.orders.mapped('orden'))])
        pedidos_pagados = {o.pos_reference: '1' if o.state != 'draft' else '0' for o in pos_order}
        lista = [{
            'id': order.id,
            'orden': order.orden,
            'cajero': order.cajero if order.cajero else "",
            'pos_name': order.pos_name,
            'pagado': pedidos_pagados.get(order.orden,'0'),
        } for order in self.orders]
        return lista

    def recibe(self, id=False):
        orders = self.orders
        if id and orders.browse(int(id)):
            order = orders.browse(int(id))
            data = order.mapped('json')
            order.received = True
            return data
        if not id:
            orders_filt = orders.filtered(lambda x: not x.received)
            orders_filt.write({'received': True})
            data = orders_filt.mapped('json')
        return data


class PosOrderTemp(models.TransientModel):
    _name = "pos.order.temp"

    session_id = fields.Many2one("pos.session","Sesion")
    json = fields.Text("Json")
    received = fields.Boolean("Ha sido recibido")
    orden = fields.Char('Referencia de orden')
    cajero = fields.Char('Cajero')
    pos_name = fields.Char('Nombre punto de ventaa')
