# -*- coding: utf-8 -*-

import uuid
from odoo import api, models, fields, _
import logging
from functools import partial
from odoo.tools.misc import formatLang

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

    def get_total_untaxed(self):
        total_untaxed = 0
        for l in self.lines:
            total_untaxed += l.price_subtotal
        return total_untaxed

    def get_amount_by_group(self):
        for order in self:
            currency = order.currency_id or order.company_id.currency_id
            fmt = partial(formatLang, self.with_context(lang=order.partner_id.lang).env, currency_obj=currency)
            res = {}
            for line in order.lines:
                price_reduce = line.price_unit * (1.0 - line.discount / 100.0)
                taxes = line.tax_ids.compute_all(price_reduce, quantity=line.qty, product=line.product_id, partner=order.partner_id)['taxes']
                for tax in line.tax_ids:
                    group = tax.tax_group_id
                    res.setdefault(group, {'amount': 0.0, 'base': 0.0})
                    for t in taxes:
                        if t['id'] == tax.id or t['id'] in tax.children_tax_ids.ids:
                            res[group]['amount'] += t['amount']
                            res[group]['base'] += t['base']
            res = sorted(res.items(), key=lambda l: l[0].sequence)
            response_amount_by_group = [(
                l[0].name, l[1]['amount'], l[1]['base'],
                fmt(l[1]['amount']), fmt(l[1]['base']),
                len(res),
            ) for l in res]
            return response_amount_by_group