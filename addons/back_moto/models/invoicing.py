

from odoo import fields, models, api
import random
import werkzeug.urls
from datetime import datetime
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger("Pos global")

class Order(models.Model):
    _inherit = "pos.order"

    fac_global = fields.Boolean("Es factura global")


class InvoiceOrder(models.TransientModel):
    _name = "pos.order.invoice"

    def get_current_pos(self):
        return [(6,0,self.env.user.pos_available.ids)]

    start_date = fields.Datetime("Desde")
    end_date = fields.Datetime("Hasta",default=fields.Datetime.now())
    re_fac = fields.Boolean("Refacturar pedidos",help="Solo se tomarán pedidos que esten dentro de una factura global")
    pos_config_ids = fields.Many2many('pos.config', 'pos_invoice_order',string="Puntos de venta",default=get_current_pos)
    current_user_pos_ids = fields.Many2many('pos.config', 'pos_invoice_default', string="Permitidos",
                                            default=get_current_pos)
    period = fields.Char("Periodo facturado",compute="cal_period")
    sobre_fac = fields.Boolean("Sobre Facturacion")
    cantidad = fields.Float("Cantidad")
    metodos_pago = fields.Many2one("pos.payment.method",string="Metodo de pago")

    def cal_period(self):
        period = ""
        if self.sobre_fac:
            period += "facturacion al " + str(self.start_date or datetime.now())
        else:
            if self.start_date:
                period +=" desde %s"%str(self.start_date)
            period += " hasta " + str(self.start_date or datetime.now())
        self.period = period

    def generate_invoice(self):
        if not self.sobre_fac:
            return self._generate_invoice()
        else:
            return self._generate_invoice_sobre()

    def _generate_invoice_sobre(self):
        invoice_ids = []
        pos_orders = self.generate_orders_random(self.cantidad,self.pos_config_ids)
        for pos,orders in pos_orders.items():
            if not orders:
                continue
            data = self.default_values_invoice()
            data.update({
                'invoice_origin': "Sucursal %s %s"%(pos,self.period),
                'l10n_mx_edi_payment_method_id': self.metodos_pago.l10n_mx_edi_payment_method_id.id
            })
            lines = []
            for order in orders:
                lines.append((0,0,self.create_line_invoice(order['name'],order['total'])))
            data['invoice_line_ids'] = lines
            invoice = self.env['account.move'].create(data)
            invoice_ids.append(invoice.id)
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        action['domain'] = [('id','in',invoice_ids)]
        action['context'] = {'default_move_type': 'out_invoice', 'move_type': 'out_invoice', 'journal_type': 'sale'}
        return action

    def _generate_invoice(self):
        invoice_ids = []
        orders = self._search_orders()
        methods = orders.mapped('payment_ids.payment_method_id.l10n_mx_edi_payment_method_id')
        method_orderes = self._split_orders_by_method(orders,methods,self.pos_config_ids)
        for method,pos_orders in method_orderes.items():
            for pos,order_ids in pos_orders.items():
                if not order_ids:
                    continue
                data = self.default_values_invoice()
                data.update({
                    'invoice_origin': "Sucursal %s %s"%(pos,self.period),
                    'l10n_mx_edi_payment_method_id': method
                })
                lines = []
                for order in order_ids:
                    lines.append((0,0,self.create_line_invoice(order.name,order.amount_total)))
                data['invoice_line_ids'] = lines
                invoice = self.env['account.move'].create(data)
                invoice_ids.append(invoice.id)
                order_ids.write({'account_move': invoice.id, 'state': 'invoiced','fac_global':True})
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        action['domain'] = [('id','in',invoice_ids)]
        action['context'] = {'default_move_type': 'out_invoice', 'move_type': 'out_invoice', 'journal_type': 'sale'}
        return action

    def _search_orders(self):
        """Return orders by period"""
        domain = [('amount_total','>',0),('session_id.config_id', 'in', self.pos_config_ids.ids)]
        if self.re_fac:
            domain += ['|',('state', 'in', ['done']),'&',('state', 'in', ['invoiced']),('fac_global', '=', True)]
        else:
            domain.append(('state','in',['done']))
        if self.start_date:
            domain.append(('date_order', '>=', self.start_date))
        if self.end_date:
            domain.append(('date_order', '<=', self.end_date))
        orders = self.env["pos.order"].search(domain)
        return orders

    def _split_orders_by_method(self,orders,methods,pos_conf):
        """Return dic of orders by method of payment"""
        # l10n_mx_edi_payment_method_id.id
        obj = self.env['pos.order']
        data = {m.id:{pos.name:obj for pos in pos_conf} for m in methods}
        for order in orders:
            metodo = order.payment_method_id.l10n_mx_edi_payment_method_id
            pos = order.config_id
            data[metodo.id][pos.name] = data[metodo.id][pos.name] | order
        return data

    def default_values_invoice(self):
        journal = self.env['account.move'].with_context(default_move_type='out_invoice')._get_default_journal()
        company_id = self.env.company
        company_currency = company_id.currency_id.id
        invoice_user = self.env.user
        partner_id = self.env['res.partner'].search([('vat', '=like', "XAXX010101000")])[:1]
        if not partner_id:
            raise UserError("No existe algún cliente con RFC a público general configurado.")
        data = {
            'move_type': 'out_invoice',
            'invoice_date': fields.Date.today(),
            'currency_id': company_currency,  # REQUIRED
            'invoice_user_id': invoice_user.id,  # REQUIRED
            'partner_id': partner_id.id,  # REQUIRED
            'partner_shipping_id': partner_id.id,  # REQUIRED
            'journal_id': journal.id,
            'company_id': company_id.id,
            'l10n_mx_edi_usage':'P01'
        }
        return data

    def create_line_invoice(self,name,total):
        product = self.env.ref('back_moto.product_global_invoice')
        data = {
            'name': name,
            'product_id': product.id,
            'product_uom_id': product.uom_id.id,
            'quantity': 1.0,
            'price_unit': total,
            'tax_ids': [(6, 0, product.taxes_id.ids)],
        }
        return data

    def generate_orders_random(self,total,pos_conf):
        data = {p.name:[] for p in pos_conf}
        names = pos_conf.mapped('name')
        minimo,maximo = 100,max(total//5,200,50000)
        sequence = random.randrange(0,100)
        while total > 0:
            ran = random.randrange(minimo,maximo)
            cantidad = min(total,ran)
            pos = random.choice(names)
            name = pos+"/{id}{ran}".format(id=self.id,ran=sequence)
            sequence += random.randrange(0,100)
            data[pos].append({'total':cantidad,'name':name})
            total -= cantidad
        return data
