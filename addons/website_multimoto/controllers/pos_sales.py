# -*- coding: utf-8 -*-

from odoo import fields, http, _
from odoo.http import request
from odoo.addons.sale.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager
import logging

_log = logging.getLogger("_-_-_-_-_-_- pos sales py :::: %s" % __name__)


class PosCustomerPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        if 'pos_order_count' in counters:
            domain = [('partner_id', '=', partner.id)]
            pos_order_count = request.env['pos.order'].sudo().search_count(domain)
            values['pos_order_count'] = pos_order_count

        return values

    @http.route(['/my/pos_sales', '/my/pos_sales/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_pos_sales(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        _log.info("PREPARE POS SALES INFORMATION.. ")
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        PosOrder = request.env['pos.order']
        domain = [
            ('partner_id', '=', partner.id)
        ]
        searchbar_sortings = {
            'date': {'label': "Fecha de compra", 'order': 'date_order desc'},
            'name': {'label': "Compra", 'order': 'name'},
        }
        if not sortby:
            sortby = 'date'
        sort_order = searchbar_sortings[sortby]['order']

        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # Count for pagination
        pos_order_count = PosOrder.sudo().search_count(domain)

        # make a pager
        pager = portal_pager(
            url="/my/pos_sales",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=pos_order_count,
            page=page,
            step=self._items_per_page
        )

        porders = PosOrder.sudo().search(domain, order=sort_order, limit=self._items_per_page, offset=pager['offset'])

        values.update({
            'date': date_begin,
            'porders': porders.sudo(),
            'page_name': 'pos_orders',
            'pager': pager,
            'default_url': '/my/pos_orders',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("website_multimoto.portal_my_pos_orders", values)

    @http.route(['/pos_order'], type='http', auth='user', website=True)
    def pos_order_details(self, **kwargs):
        pos_token = kwargs['stoken'] or ""
        PosOrder = request.env['pos.order'].sudo().search([('token_portal', 'ilike', pos_token)])[:1]
        # _log.info("pos ordeR: :: %s " % PosOrder)
        values = {
            'porder': PosOrder,
            'page_name': 'pos_order',
            'default_url': '/pos_order',
        }
        return request.render("website_multimoto.pos_portal_order_content", values)