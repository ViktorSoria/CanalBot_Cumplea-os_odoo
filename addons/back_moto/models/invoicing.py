

from odoo import fields, models, api, _
import random
import werkzeug.urls
from datetime import datetime
from odoo.exceptions import UserError, ValidationError
from collections import defaultdict
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
            'l10n_mx_edi_usage':'P01',
            "is_global":True
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
        minimo,maximo = 100,max(min(total//5,50000),200)
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


class Invoice(models.Model):
    _inherit = "account.move"

    is_global = fields.Boolean("Es factura global")

    @api.depends('posted_before', 'state', 'journal_id', 'date')
    def _compute_name(self):
        super()._compute_name()
        is_global = self.filtered(lambda m: m.is_global)
        for move in is_global.filtered(lambda m: 'GLOB' not in m.name):
            move.name = move.name.replace("INV/","INV/GLOB/")
        for move in self-is_global:
            move.name = move.name.replace("INV/GLOB/","INV/")

    def _get_last_sequence(self, relaxed=False):
        """Retrieve the previous sequence.

        This is done by taking the number with the greatest alphabetical value within
        the domain of _get_last_sequence_domain. This means that the prefix has a
        huge importance.
        For instance, if you have INV/2019/0001 and INV/2019/0002, when you rename the
        last one to FACT/2019/0001, one might expect the next number to be
        FACT/2019/0002 but it will be INV/2019/0002 (again) because INV > FACT.
        Therefore, changing the prefix might not be convenient during a period, and
        would only work when the numbering makes a new start (domain returns by
        _get_last_sequence_domain is [], i.e: a new year).

        :param field_name: the field that contains the sequence.
        :param relaxed: this should be set to True when a previous request didn't find
            something without. This allows to find a pattern from a previous period, and
            try to adapt it for the new period.

        :return: the string of the previous sequence or None if there wasn't any.
        """
        self.ensure_one()
        if self._sequence_field not in self._fields or not self._fields[self._sequence_field].store:
            raise ValidationError(_('%s is not a stored field', self._sequence_field))
        where_string, param = self._get_last_sequence_domain(relaxed)
        if self.id or self.id.origin:
            where_string += " AND id != %(id)s "
            param['id'] = self.id or self.id.origin
        q1 = "SELECT sequence_prefix FROM {table} {where_string} ORDER BY id DESC LIMIT 1".format(table=self._table,
            where_string=where_string,)
        self.env.cr.execute(q1, param)
        pref = self.env.cr.fetchone()[0] or ''
        _logger.warning(pref)
        query = """
            UPDATE {table} SET write_date = write_date WHERE id = (
                SELECT id FROM {table}
                {where_string}
                AND sequence_prefix in ({pref}) 
                ORDER BY sequence_number DESC
                LIMIT 1
            )
            RETURNING {field};
        """.format(
            table=self._table,
            where_string=where_string,
            field=self._sequence_field,
            pref="'{}','{}','{}' ".format(pref,pref.replace('INV/','INV/GLOB/'),pref.replace('INV/GLOB/','INV/'))
        )

        self.flush([self._sequence_field, 'sequence_number', 'sequence_prefix'])
        self.env.cr.execute(query, param)
        return (self.env.cr.fetchone() or [None])[0]