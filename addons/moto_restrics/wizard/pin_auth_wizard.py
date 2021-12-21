# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging
from lxml import etree
import base64
from odoo.exceptions import ValidationError

_log = logging.getLogger("__ PIN AUTHENTICATOR:: %s" % __name__)


class ActionPinAuth(models.TransientModel):
    _name = "action.pin.auth"
    _description = "Autenticación de responsable"

    pin = fields.Integer(string="PIN", required=True)

    @api.model
    def _check_permission(self, pin=0):
        if pin == 0:
            return False
        admin_id = self.env['res.users'].sudo().search([('clave', '=', pin)])
        return True if admin_id else False

    def do_process(self):
        if self._check_permission(self.pin):
            rec = self.env[self._context['ori_model']].browse(self._context['ori_id'])
            method = self._context['ori_method']
            return getattr(rec, method)()
        else:
            raise ValidationError("No está autorizado para realizar la operación.")
