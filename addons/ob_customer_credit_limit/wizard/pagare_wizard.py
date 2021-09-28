# -*- coding: utf-8 -*-
from odoo import models, fields


class Invoice(models.Model):
    _inherit = "account.move"

    def action_pagare(self):
        return {
            'name': 'Pagaré',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'pagare.wizard',
            'target': 'new',
            'context': {'default_move_id':self.id,'default_fecha':self.invoice_date},
        }


class PagareWizard(models.TransientModel):
    _name = "pagare.wizard"

    move_id = fields.Many2one('account.move', string="Factura")
    fecha = fields.Date("Fecha de venta")
    sucursal = fields.Many2one("res.partner","Lugar Emisión")
    currency = fields.Many2one("res.currency","Moneda",related="move_id.currency_id")
    monto = fields.Monetary("Monto",related="move_id.amount_residual",currency_field="currency")
    fecha_limite = fields.Date("Fecha limite",related="move_id.invoice_date_due")
    domicilio = fields.Char("domicilio",compute="get_domi")
    sucursal_name = fields.Char("sucursal dom",compute="get_domi")

    def get_domi(self):
        partner_id = self.move_id.partner_id
        self.domicilio = "{} #{} Col. {} {} {}, {}".format(partner_id.street_name or '',
                                                               partner_id.street_number or 'SN',
                                                               partner_id.l10n_mx_edi_colony or '',
                                                               ('C.P. '+partner_id.zip) if partner_id.zip else '',
                                                               partner_id.city_id.name or partner_id.city or '',
                                                               partner_id.state_id.name or '')
        partner_id = self.sucursal
        self.sucursal_name = "{}, {}".format(partner_id.city_id.name or partner_id.city or '',partner_id.state_id.name or '')

    def generate_report(self):
        return self.env.ref('ob_customer_credit_limit.report_pagare').report_action(self.ids)
