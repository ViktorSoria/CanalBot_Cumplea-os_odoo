# -*- coding: utf-8 -*-
from odoo import models
import logging
_log = logging.getLogger("___name: %s" % __name__)


class PosOrderMmRestricted(models.Model):
    _inherit = "pos.order"

    def restricted_refund(self):
        return {
            'name': "Introduce PIN de administrador",
            'type': 'ir.actions.act_window',
            'res_model': 'action.pin.auth',
            'target': 'new',
            'view_mode': 'form',
            'context': {
                'ori_method': "refund",
                'ori_id': self.id,
                'ori_model': "pos.order"
            }
        }