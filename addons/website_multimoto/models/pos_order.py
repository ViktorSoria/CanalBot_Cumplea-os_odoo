# -*- coding: utf-8 -*-

import uuid
from odoo import api, models, fields, _
import datetime
import calendar
import logging

_log = logging.getLogger("pos_order (%s) -------> " % __name__)


class PosWebsite(models.Model):
    _inherit = "pos.order"

    token_portal = fields.Char(string="token")

    def get_portal_url(self):
        _log.info("GENERANDO URL ")
        url = "%s/pos_order?stoken=%s" % (self.env['ir.config_parameter'].sudo().get_param('web.base.url'), self._get_portal_token())
        return url

    def _get_portal_token(self):
        if not self.token_portal:
            token = str(uuid.uuid4())
            _log.info("")
            self.sudo().write({'token_portal': token})
        return self.token_portal
