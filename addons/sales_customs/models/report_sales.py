from odoo import api, models, fields, _
from odoo.exceptions import UserError
from datetime import datetime
from odoo.tools import float_is_zero
import logging

_log = logging.getLogger("sale_customs (%s) -------> " % __name__)

months = [('1', 'Enero'), ('2', 'Febrero'), ('3', 'Marzo'), ('4', 'Abril'), ('5', 'Mayo'), ('6', 'Junio'), ('7', 'Julio'), ('8', 'Agosto'), ('9', 'Septiembre'), ('10', 'Octubre'), ('11', 'Noviembre'), ('12', 'Diciembre')]


class ReportSalesCustomWizard(models.TransientModel):
    _name = "wizard.report.sales.custom"

    partner_ids = fields.Many2many('res.partner', string='Clientes')
    all_partners = fields.Boolean('Todos Los clientes', default='True')
    date_start = fields.Date(string='Desde')
    date_end = fields.Date(string='Hasta')
    options = fields.Selection([('all','Todas (Pedidos de Venta y Punto de Venta)'),('sale','Pedidos de Ventas'),('pos','Pedidos del Punto de Venta')], string="Tipos de Pedidos", default='all')

    def search_records(self):
        dic = {}
        if self.options == 'all' or self.options == 'sale':
            invoices = self.env['account.move'].sudo().search([('invoice_date', '>=', self.date_start), ('invoice_date', '<=', self.date_end),  ('state', '=', 'posted'), ('move_type', 'in', ['out_invoice', 'in_refund'])])
            for invoice in invoices:
                partner_id = invoice.partner_id.id
                key = str(partner_id) + " - " + str(invoice.invoice_date.month) + " - " + str(invoice.team_id.id)
                if key in dic:
                    dic[key].update({
                        'total': dic[key]['total'] + invoice.amount_total
                    })
                else:
                    dic[key] = {
                        'partner_id': partner_id,
                        'total': invoice.amount_total,
                        'month': str(invoice.invoice_date.month),
                        'sale_team': invoice.team_id.id
                    }
        if self.options == 'all' or self.options == 'pos':
            pos_orders = self.env['pos.order'].sudo().search([('date_order', '>=', self.date_start), ('date_order', '<=', self.date_end), ('state', 'in', ['paid','done'])])
            for order in pos_orders:
                partner_id = order.partner_id.id
                key = str(partner_id) + " - " + str(order.date_order.month) + " - " + str(order.crm_team_id.id)
                if key in dic:
                    dic[key].update({
                        'total': dic[key]['total'] + order.amount_total
                    })
                else:
                    dic[key] = {
                        'partner_id': partner_id,
                        'total': order.amount_total,
                        'month': str(order.date_order.month),
                        'sale_team': order.crm_team_id.id
                    }
        return self.with_context(dic=dic).create_view()

    def create_view(self):
        dic = self.env.context.get('dic', {})
        recs = self.env['report.sales.custom'].create(dic.values())
        return {
            'name': _('Reporte de Ventas por cliente'),
            'type': 'ir.actions.act_window',
            'view_type': 'list',
            'view_mode': 'pivot,list',
            'res_model': 'report.sales.custom',
            'views': [(self.env.ref('sales_customs.view_report_sale_custom_pivot').id, 'pivot'), (self.env.ref('sales_customs.view_report_sale_custom_tree').id, 'list')],
            'search_view_id': self.env.ref('sales_customs.view_report_sale_custom_search').id,
            # 'context': {'search_default_client': 1, 'search_default_sale_t': 2},
            'domain': [('id', 'in', recs.ids)]
        }


class ReportSalesComisionWizard(models.TransientModel):
    _name = "wizard.report.sales.comision"

    partner_ids = fields.Many2many('res.partner', string='Clientes')
    all_partners = fields.Boolean('Todos Los clientes', default='True')
    date_start = fields.Date(string='Desde')
    date_end = fields.Date(string='Hasta')
    options = fields.Selection([('all','Todas (Pedidos de Venta y Punto de Venta)'),('sale','Pedidos de Ventas'),('pos','Pedidos del Punto de Venta')], string="Tipos de Pedidos", default='all')

    def search_records(self):
        dic = {}
        if self.options == 'all' or self.options == 'sale':
            invoices = self.env['account.move'].sudo().search([('invoice_date', '>=', self.date_start), ('invoice_date', '<=', self.date_end),  ('state', '=', 'posted'), ('move_type', 'in', ['out_invoice', 'in_refund']),('payment_date', '!=', None)])
            for invoice in invoices:
                key = str(invoice.id) + 'account_move'
                dic[key] = {
                    'name': invoice.name,
                    'partner_id': invoice.partner_id.id,
                    'user_id': invoice.invoice_user_id.id,
                    'total': invoice.amount_total,
                    'date': invoice.payment_date,
                    'sale_team': invoice.team_id.id
                }
        if self.options == 'all' or self.options == 'pos':
            pos_orders = self.env['pos.order'].sudo().search([('date_order', '>=', self.date_start), ('date_order', '<=', self.date_end), ('state', 'in', ['paid','done'])])
            for order in pos_orders:
                key = str(order.id) + "pos_order"
                dic[key] = {
                    'name': order.name,
                    'partner_id': order.partner_id.id,
                    'user_id': order.user_id.id,
                    'total': order.amount_total,
                    'date': order.date_order.date(),
                    'sale_team': order.crm_team_id.id
                }
        return self.with_context(dic=dic).create_view()

    def create_view(self):
        dic = self.env.context.get('dic', {})
        recs = self.env['report.sales.comision'].create(dic.values())
        return {
            'name': _('Reporte de Comisión'),
            'type': 'ir.actions.act_window',
            'view_type': 'list',
            'view_mode': 'pivot,list',
            'res_model': 'report.sales.comision',
            'views': [(self.env.ref('sales_customs.view_report_sale_comision_pivot').id, 'pivot'), (self.env.ref('sales_customs.view_report_sale_comision_tree').id, 'list')],
            'search_view_id': self.env.ref('sales_customs.view_report_sale_comision_search').id,
            # 'context': {'search_default_client': 1, 'search_default_sale_t': 2},
            'domain': [('id', 'in', recs.ids)]
        }


class ReportSalesComisionLine(models.TransientModel):
    _name = "report.sales.comision"

    name = fields.Char('Referencia')
    partner_id = fields.Many2one('res.partner','Cliente')
    user_id = fields.Many2one('res.users','Vendedor')
    total = fields.Float('Total')
    sale_team = fields.Many2one('crm.team','Equipo de Ventas')
    date = fields.Date('Fecha')


class ReportSalesCustomLine(models.TransientModel):
    _name = "report.sales.custom"

    partner_id = fields.Many2one('res.partner','Cliente')
    total = fields.Float('Total')
    sale_team = fields.Many2one('crm.team','Equipo de Ventas')
    month = fields.Selection(months, 'Mes')


class AccountMovePaymentDate(models.Model):
    _inherit = "account.move"

    payment_date = fields.Date('Fecha de Pago')

    @api.depends('amount_residual')
    def get_last_date_payment(self):
        for rec in self:
            if float_is_zero(rec.amount_residual, precision_digits=rec.currency_id.decimal_places):
                payments = rec.sudo()._get_reconciled_info_JSON_values()
                dates = []
                for payment in payments:
                    dates.append(payment['date'])
                date_max = max(dates) if len(dates) > 0 else None
                rec.payment_date = date_max
            else:
                rec.payment_date = None



