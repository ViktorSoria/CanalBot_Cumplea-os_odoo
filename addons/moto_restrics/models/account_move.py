# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import Warning, UserError, ValidationError
import logging
_log = logging.getLogger("___name: %s" % __name__)


class AccountMoveMmRestricted(models.Model):
    _inherit = "account.move"

    def restricted_button_cancel(self):
        return {
            'name': "Introduce PIN de administrador",
            'type': 'ir.actions.act_window',
            'res_model': 'action.pin.auth',
            'target': 'new',
            'view_mode': 'form',
            'context': {
                'ori_method': "button_cancel",
                'ori_id': self.id,
                'ori_model': "account.move"
            }
        }

    def restricted_button_cancel_posted_moves(self):
        return {
            'name': "Introduce PIN de administrador",
            'type': 'ir.actions.act_window',
            'res_model': 'action.pin.auth',
            'target': 'new',
            'view_mode': 'form',
            'context': {
                'ori_method': "button_cancel_posted_moves",
                'ori_id': self.id,
                'ori_model': "account.move"
            }
        }

    def restricted_action_post(self):
        if self.move_type in ['out_refund', 'in_refund']:
            return {
                'name': "Introduce PIN de administrador",
                'type': 'ir.actions.act_window',
                'res_model': 'action.pin.auth',
                'target': 'new',
                'view_mode': 'form',
                'context': {
                    'ori_method': "action_post",
                    'ori_id': self.id,
                    'ori_model': "account.move",
                }
            }
        else:
            self.action_post()
