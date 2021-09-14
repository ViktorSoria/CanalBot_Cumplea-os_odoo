# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import AccessDenied
import logging

_logger = logging.getLogger("Credito")


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    autorizado = fields.Boolean("Autorizado")
    auto_usr = fields.Many2one("res.users", string="Autorizado por")
    necesita = fields.Boolean("Necesita Autorizacion")
    amount_due = fields.Monetary(related='partner_id.amount_due', currency_field='company_currency_id')
    company_currency_id = fields.Many2one(string='Company Currency', readonly=True,
        related='company_id.currency_id')

    def autorizar(self):
        self.write({'autorizado':True,'auto_usr':self.env.user.id})

    def action_confirm(self):
        '''
        Check the partner credit limit and exisiting due of the partner
        before confirming the order. The order is only blocked if exisitng
        due is greater than blocking limit of the partner.
        '''
        partner_id = self.partner_id
        total_amount = self.amount_due + self.amount_total
        _logger.warning(total_amount)
        _logger.warning(partner_id.credit_check)
        existing_move = self.invoice_ids
        if partner_id.credit_check and not existing_move:
            context = dict(self.env.context or {})
            context['default_sale_id'] = self.id
            if partner_id.credit_warning <= total_amount and partner_id.credit_blocking > total_amount:
                view_id = self.env.ref('ob_customer_credit_limit.view_warning_wizard_form')
                context['message'] = "Se excedio el limiti de credito de advertencia. Desea Continuar?"
                if not self._context.get('warning'):
                    return {
                        'name': 'Warning',
                        'type': 'ir.actions.act_window',
                        'view_mode': 'form',
                        'res_model': 'warning.wizard',
                        'view_id': view_id.id,
                        'target': 'new',
                        'context': context,
                    }
            elif partner_id.credit_blocking <= total_amount:
                if self.autorizado:
                    if not self._context.get('warning'):
                        context['message'] = "Esta venta ya fue aprovada. Desea continuar?"
                        view_id = self.env.ref('ob_customer_credit_limit.view_warning_wizard_form')
                    else:
                        return super(SaleOrder, self).action_confirm()
                else:
                    context['message'] = "Limite de credito excedido. Necesita Autorización"
                    view_id = self.env.ref('ob_customer_credit_limit.view_den_wizard_form')
                return {
                    'name': 'Warning',
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'warning.wizard',
                    'view_id': view_id.id,
                    'target': 'new',
                    'context': context,
                }
        return super(SaleOrder, self).action_confirm()
