# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    cargo_vencimiento = fields.Float("charge_owed_invoices", default=4.4)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update({
            'cargo_vencimiento': float(params.get_param('cargo_vencimiento')) or 4.4,
        })
        return res

    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param('cargo_vencimiento', self.cargo_vencimiento)
        super(ResConfigSettings, self).set_values()