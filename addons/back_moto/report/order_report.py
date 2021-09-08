

from odoo import fields, models, api
from odoo.exceptions import UserError
import xlrd
import tempfile
import csv
from io import StringIO
import base64
import logging

_logger = logging.getLogger("Report")


class Report_order(models.TransientModel):
    _name = "report.order"

    # def _default_start_date(self):
    #     """ Find the earliest start_date of the latests sessions """
    #     # restrict to configs available to the user
    #     config_ids = self.env['pos.config'].search([]).ids
    #     # exclude configs has not been opened for 2 days
    #     self.env.cr.execute("""
    #         SELECT
    #         max(start_at) as start,
    #         config_id
    #         FROM pos_session
    #         WHERE config_id = ANY(%s)
    #         AND start_at > (NOW() - INTERVAL '5 DAYS')
    #         GROUP BY config_id
    #     """, (config_ids,))
    #     latest_start_dates = [res['start'] for res in self.env.cr.dictfetchall()]
    #     # earliest of the latest sessions
    #     return latest_start_dates and min(latest_start_dates).replace(minute=0,hour=0,second=0) or fields.Datetime.now().replace(minute=0,hour=0,second=0)

    start_date = fields.Date("Fecha de Inicio",required=True, default=fields.Date.today().replace(day=1))
    end_date = fields.Date("Fecha de Finalizacion",required=True, default=fields.Date.today())
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
        data = {'date_start': self.start_date, 'date_stop': self.end_date, 'config_ids': self.pos_config_ids.ids,
                'team_ids': self.team_ids.ids}
        return self.env.ref('back_moto.report_consolidado').report_action([], data=data)


class ParticularReport(models.AbstractModel):
    _name = 'report.back_moto.template_consolidado'

    def _get_report_values(self, docids, data=None):
        domain = [('create_date','>=',data['date_start']),('create_date','<=',data['date_stop']),('session_id.config_id','in',data['config_ids']),('state','not in',['draft','cancel'])]
        pos_lines_fac = self.env['pos.order'].search(domain+[('to_invoice','=',False),('amount_total','>',0)])
        pos_lines_no_fac = self.env['pos.order'].search(domain+[('to_invoice','=',True),('amount_total','>',0)])
        pos_lines_dev = self.env['pos.order'].search(domain+[('amount_total','<=',0)])
        domain = [('invoice_date','>=',data['date_start']),('invoice_date','<=',data['date_stop']),('team_id','in',data['team_ids']),('state','=','posted')]
        fact = self.env['account.move'].search(domain+[('move_type','=','out_invoice')])
        nc = self.env['account.move'].search(domain+[('move_type','=','out_refund')])
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