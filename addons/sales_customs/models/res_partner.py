# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
import datetime
import calendar
import logging

_log = logging.getLogger("stock_picking (%s) -------> " % __name__)


class ResPartnerCustom(models.Model):
    _inherit = "res.partner"

    phone = fields.Char(required=True)


class ResUsersCustom(models.Model):
    _inherit = "res.users"

    pos_available = fields.Many2many('pos.config', string="Puntos de Venta")
    team_available = fields.Many2many('crm.team', string="Equipos de Venta", default=lambda self: self.sale_team_id)

    def all_pos(self):
        self.pos_available = self.env['pos.config'].search([])

    def all_teams(self):
        self.pos_available = self.env['crm.team'].search([])

