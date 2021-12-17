# -*- coding: utf-8 -*-

from odoo import fields, http, _
from odoo.http import request
from odoo.addons.sale.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager
from collections import OrderedDict
import logging

_log = logging.getLogger("_-_-_-_-_-_- pos sales py :::: %s" % __name__)


class PosCustomerPortal(CustomerPortal):

    @http.route(['/my/invoices', '/my/invoices/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_invoices(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        AccountInvoice = request.env['account.move']

        domain = [
            ('move_type', 'in', ('out_invoice', 'out_refund', 'in_invoice', 'in_refund', 'out_receipt', 'in_receipt')),
            ('state','not in',['cancel'])
        ]

        searchbar_sortings = {
            'date': {'label': _('Date'), 'order': 'invoice_date desc'},
            'duedate': {'label': _('Due Date'), 'order': 'invoice_date_due desc'},
            'name': {'label': _('Reference'), 'order': 'name desc'},
            'state': {'label': _('Status'), 'order': 'state'},
        }
        # default sort by order
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'invoices': {'label': _('Invoices'), 'domain': [('move_type', '=', ('out_invoice', 'out_refund'))]},
            'bills': {'label': _('Bills'), 'domain': [('move_type', '=', ('in_invoice', 'in_refund'))]},
        }
        # default filter by value
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']

        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        invoice_count = AccountInvoice.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/invoices",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=invoice_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        invoices = AccountInvoice.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_invoices_history'] = invoices.ids[:100]

        values.update({
            'date': date_begin,
            'invoices': invoices,
            'page_name': 'invoice',
            'pager': pager,
            'default_url': '/my/invoices',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
        })
        return request.render("account.portal_my_invoices", values)

    def _prepare_portal_layout_values(self):
        res = super()._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        res['partner_total'] = partner.total_invoiced * 1.16
        res['partner_credit'] = partner.credit
        return res

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
        values = {
            'porder': PosOrder,
            'page_name': 'pos_order',
            'default_url': '/pos_order',
        }
        return request.render("website_multimoto.pos_portal_order_content", values)