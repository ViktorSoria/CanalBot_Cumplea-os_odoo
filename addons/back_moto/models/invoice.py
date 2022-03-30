

from odoo import fields, models, api
from odoo.exceptions import UserError
import xlrd
import tempfile
import csv
from io import StringIO
import base64
import logging

_logger = logging.getLogger("Moto Control")


class Inovice(models.Model):
    _inherit = "account.move"

    def action_process_edi_web_services(self):
        docs = self.edi_document_ids.filtered(lambda d: d.state in ('to_send', 'to_cancel'))
        if 'blocking_level' in self.env['account.edi.document']._fields:
            docs = docs.filtered(lambda d: d.blocking_level != 'error')
        # datos de facturacion
        if self.env.context.get('return_message'):
            for invoice in self.filtered(lambda l: l.edi_state == 'to_send'):
                mensaje = ""
                if invoice.partner_id and not invoice.partner_id.vat:
                    mensaje += "EL cliente no tiene RFC\n"
                if invoice.l10n_mx_edi_usage == 'P01':
                    mensaje += "EL uso del CFDI esta establecido por definir\n"
                if invoice.l10n_mx_edi_payment_method_id.code == '99':
                    mensaje += "La forma de pago es por definiro\n"
                if mensaje:
                    mensaje += "¿Desea continuar?"
                    return{
                        'name': 'Confirmacion de datos',
                        'type': 'ir.actions.act_window',
                        'view_mode': 'form',
                        'res_model': 'message.wizard.invoice',
                        'target': 'new',
                        'context': {'default_name':mensaje,'default_invoice_ids':self.ids}
                    }
        docs._process_documents_web_services(with_commit=False)
        self._compute_cfdi_values()


class Message(models.TransientModel):
    _name = 'message.wizard.invoice'


    name = fields.Text(string="Message",readonly=True)
    invoice_ids = fields.Many2many("account.move","invoice_message_rel",string="Facturas")

    def confirm(self):
        self.invoice_ids.with_context(return_message=False).action_process_edi_web_services()