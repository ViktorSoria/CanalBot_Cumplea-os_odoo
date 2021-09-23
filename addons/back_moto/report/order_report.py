

from odoo import fields, models, api
from odoo.exceptions import UserError
from datetime import datetime,timezone,timedelta
import pytz
import logging

_logger = logging.getLogger("Report")


class Report_order(models.TransientModel):
    _name = "report.order"

    def _default_start_date(self):
        date = datetime.now().replace(minute=0,hour=0,second=0,day=1)
        tz_str = self.env.user.tz or 'America/Mexico_City'
        tz = pytz.timezone(tz_str)
        date = tz.localize(date)
        date = date.astimezone(tz=timezone.utc)
        date = date.replace(tzinfo=None)
        return date

    start_date = fields.Datetime("Fecha de Inicio",required=True, default=_default_start_date)
    end_date = fields.Datetime("Fecha de Finalizacion",required=True, default=fields.Datetime.now())
    pos_config_ids = fields.Many2many('pos.config', 'pos_report_order', 'report','pos',string="Puntos de venta",
        default=lambda s: s.env['pos.config'].search([]))
    team_ids = fields.Many2many('crm.team', 'crm_report_order', 'report','pos',string="Equipos de Ventas",
        default=lambda s: s.env['crm.team'].search([]))

    @api.onchange('start_date')
    def _onchange_start_date(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            self.end_date = self.start_date

    @api.onchange('end_date')
    def _onchange_end_date(self):
        if self.end_date and self.end_date < self.start_date:
            self.start_date = self.end_date

    def generate_report(self):
        fecha_inicio = self.start_date
        fecha_fin = self.end_date
        data = {'date_start': fecha_inicio, 'date_stop': fecha_fin, 'config_ids': self.pos_config_ids.ids,
                'team_ids': self.team_ids.ids}
        return self.env.ref('back_moto.report_consolidado').report_action([], data=data)


class ParticularReport(models.AbstractModel):
    _name = 'report.back_moto.template_consolidado'

    def _get_report_values(self, docids, data=None):
        domain = [('create_date','>=',data['date_start']),('create_date','<=',data['date_stop']),('session_id.config_id','in',data['config_ids']),('state','not in',['draft','cancel'])]
        pos_lines_fac = self.env['pos.order'].search(domain+[('to_invoice','=',False),('amount_total','>',0)])
        pos_lines_no_fac = self.env['pos.order'].search(domain+[('to_invoice','=',True),('amount_total','>',0)])
        pos_lines_dev = self.env['pos.order'].search(domain+[('amount_total','<=',0)])
        pos = pos_lines_fac + pos_lines_no_fac + pos_lines_dev
        move_pos = pos.mapped('account_move')
        domain = [('invoice_date','>=',(data['date_start']-timedelta(hours=5)).date()),('invoice_date','<=',(data['date_stop']-timedelta(hours=6)).date()),('team_id','in',data['team_ids']),('state','=','posted')]
        fact = self.env['account.move'].search(domain+[('move_type','=','out_invoice')]) -move_pos
        nc = self.env['account.move'].search(domain+[('move_type','=','out_refund')]) -move_pos
        domain = [('date','>=',data['date_start']),('date','<=',data['date_stop']),('state','=','done')]
        gastos = self.env['hr.expense'].search(domain)
        pos = pos_lines_fac + pos_lines_no_fac + pos_lines_dev
        fac = fact+nc
        total_method = self._compute_totals(pos,fac,gastos)
        data.update({
            "pos": {'facturado':pos_lines_fac,'no_facturado':pos_lines_no_fac,'devoluciones':pos_lines_dev},
            'sale': {'facturas':fact,'nc':nc},
            'gastos':gastos,
            'metodo':total_method,
            "currency": self.env.user.company_id.currency_id
        })
        _logger.warning(data)
        return data

    def _compute_totals(self,pos,fac,gastos):
        met = {}
        ### calcule pos
        for order in pos:
            for pay in order.payment_ids:
                met[pay.payment_method_id.l10n_mx_edi_payment_method_id.name] = met.get(pay.payment_method_id.l10n_mx_edi_payment_method_id.name,0) + pay.amount
        ### calcule fac
        for invoice in fac:
            met[invoice.l10n_mx_edi_payment_method_id.name] = met.get(invoice.l10n_mx_edi_payment_method_id.name, 0) + invoice.amount_total
        return met