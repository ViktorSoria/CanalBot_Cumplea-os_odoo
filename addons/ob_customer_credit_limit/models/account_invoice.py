# -*- coding: utf-8 -*-
from odoo import models, fields, _, api
from odoo.exceptions import AccessDenied
import logging

_logger = logging.getLogger("Facturas vencidas")


class Inovice(models.Model):
    _inherit = 'account.move'

    invoice_origin_id = fields.Many2one("account.move", string="Factura Origen Cargo")
    invoice_cargo_ids = fields.One2many("account.move", 'invoice_origin_id', string="Cargo por factura vencida")
    es_cargo = fields.Boolean("Es cargo")

    @api.model
    def cron_calcule_cargos(self):
        # tasa de adeudo
        porcentaje = self.env['ir.config_parameter'].sudo().get_param('cargo_vencimiento') or 4.4
        owed_rate = (float(porcentaje)/100)+1
        # Facturas adeudadas al día de hoy.
        inv_domain = [
            ('move_type', '=', 'out_invoice'),
            ('es_cargo', '=', False),
            ('state', '=', 'posted'),
            ('invoice_date_due', '<', fields.Date.today()),
            ('payment_state', 'in', ['not_paid', 'partial'])
        ]
        invoices_waiting4payment = self.env['account.move'].search(inv_domain)
        invoices_waiting4payment = invoices_waiting4payment.filtered(lambda inv: inv.invoice_date_due != inv.invoice_date)

        if not invoices_waiting4payment or len(invoices_waiting4payment) <= 0:
            return

        journal_id = self.env['account.journal'].search([('name', 'like', "Facturas de cliente")])
        product_id_charge = self.env.ref("ob_customer_credit_limit.invoice_wo_payment_product_charge")

        invoices_wo_charges = invoices_waiting4payment.filtered(lambda f: not f.invoice_cargo_ids)
        invoices_w_charges = invoices_waiting4payment.filtered(lambda f: f.invoice_cargo_ids and any([s != 'cancel' for s in f.invoice_cargo_ids.mapped('state')]))

        extra_charge_days = 30
        # Invoice without charges
        for iwoc in invoices_wo_charges:
            #crear factura de cargo
            owed_total = iwoc.amount_residual * owed_rate
            _logger.info("TOTAL ADEUDADO::: %s " % owed_total)
            # taxes = iwoc.invoice_line_ids.mapped('tax_ids').ids
            new_invoice = {
                'partner_id': iwoc.partner_id.id,
                'l10n_mx_edi_payment_method_id': iwoc.l10n_mx_edi_payment_method_id.id,
                'l10n_mx_edi_payment_policy': iwoc.l10n_mx_edi_payment_policy,
                'invoice_date': fields.Date.today(),
                'move_type': "out_invoice",
                'journal_id': journal_id.id,
                'invoice_line_ids': [(0, 0, {
                    'product_id': product_id_charge.id,
                    'quantity': 1,
                    'product_uom_id': 1,
                    'price_unit': owed_total
                })],
            }
            iwoc.invoice_cargo_ids = [(0, 0, new_invoice)]

        # Invoices with charges
        for iwc in invoices_w_charges:
            owed_total = iwc.amount_residual * owed_rate
            _logger.info("Factura con pagos atrasados %s" % iwc)
            # If we have extra owed charges  in open state add new line in first.
            # Buscamos facturas de cargos extras que estén en borrador.
            open_inv = iwc.invoice_cargo_ids.filtered(lambda f: f.state == 'draft')[:1]
            posted_inv = iwc.invoice_cargo_ids.filtered(lambda f: f.state == 'posted')[:1]

            if open_inv:
                new_line_dict = {
                    'product_id': product_id_charge.id,
                    'quantity': 1,
                    'product_uom_id': 1,
                    'price_unit': owed_total
                }
                open_inv.invoice_line_ids = [(0, 0, new_line_dict)]
            elif posted_inv:
                new_invoice = {
                    'partner_id': iwc.partner_id.id,
                    'l10n_mx_edi_payment_method_id': iwc.l10n_mx_edi_payment_method_id.id,
                    'l10n_mx_edi_payment_policy': iwc.l10n_mx_edi_payment_policy,
                    'invoice_date': fields.Date.today(),
                    'move_type': "out_invoice",
                    'journal_id': journal_id.id,
                    'invoice_line_ids': [(0, 0, {
                        'product_id': product_id_charge.id,
                        'quantity': 1,
                        'product_uom_id': 1,
                        'price_unit': owed_total
                    })],
                }
                iwc.invoice_cargo_ids = [(0, 0, new_invoice)]

            # else  if we have extra owed charges in paid or published add new invoice
            # abierto = iwc.invoice_cargo_ids.filtered()