# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError, ValidationError


class PurchaseOrderCustom(models.Model):
    _inherit = "purchase.order"

    def import_xml_invoice(self):
        return {
            'name': _('Importar lineas desde XML'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'xml.to.pol',
            'target': 'new',
            'context': {
                'purchase_id': self.id
            },
        }


