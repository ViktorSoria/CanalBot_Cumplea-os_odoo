# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import AccessDenied
import logging

_logger = logging.getLogger("Facturas vencidas")


class Inovice(models.Model):
    _inherit = 'account.move'

    invoice_origin_id = fields.Many2one("account.move", string="Factura Origen Cargo")
    invoice_cargo_ids = fields.One2many("account.move", 'invoice_origin_id',string="Cargo por factura vencida")
    es_cargo = fields.Boolean("Es cargo")

    def cron_calcule_cargos(self):
        porcentaje = self.env['ir.config_parameter'].sudo().get_param('cargo_vencimiento') or 4.4
        porcentaje = float(porcentaje)
        facturas = self.env['account.move'].search([('move_type','=','out_invoice'),('es_cargo','=',False),
                                                    ('es_cargo','=',False),('state','=','posted'),('inovice_date_due','<',fields.Date.today()),
                                                    ('payment_state','in',['not_paid','partial'])])
        nuevas = facturas.filtered(lambda f: not f.invoice_cargo_ids)
        con_cargos = facturas.filtered(lambda f: f.invoice_cargo_ids and any([s != 'cancel' for s in f.invoice_cargo_ids.mapped('state')]))
        for n in nuevas:
            #crear factura de cargo
            pass
        for c in con_cargos:
            abierto = c.invoice_cargo_ids.filtered()