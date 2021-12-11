
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.web import Home
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.website_sale_stock.controllers.main import WebsiteSaleStock
from odoo.tools.translate import _
from odoo.exceptions import ValidationError
import logging

_log = logging.getLogger(__name__)


class WebsiteSaleStockCus(WebsiteSaleStock):
    @http.route()
    def payment_transaction(self, *args, **kwargs):
        """ Payment transaction override to double check cart quantities before
        placing the order
        """
        order = request.website.sale_get_order()
        values = []
        for line in order.order_line:
            if line.product_id.type == 'product' and line.product_id.inventory_availability in ['always', 'threshold']:
                cart_qty = sum(order.order_line.filtered(lambda p: p.product_id.id == line.product_id.id).mapped('product_uom_qty'))
                ware = request.env['stock.warehouse'].sudo().search([]).ids
                avl_qty = line.product_id.with_context(warehouse=ware).virtual_available
                if cart_qty > avl_qty:
                    values.append(_(
                        'Ha solicitado %(quantity)s productos, pero hay %(available_qty)s disponible.',
                        quantity=cart_qty,
                        available_qty=avl_qty if avl_qty > 0 else 0
                    ))
        if values:
            raise ValidationError('. '.join(values) + '.')
        return super(WebsiteSaleStock, self).payment_transaction(*args, **kwargs)


class WebsiteBackend(Home):

    @http.route('/', type='http', auth="public", website=True, sitemap=True)
    def index(self, **kw):
        # prefetch all menus (it will prefetch website.page too)
        ip = request.env['ir.config_parameter'].sudo().get_param('public_domain')
        if ip and ip not in request.httprequest.url_root:
            return request.redirect(request.httprequest.url_root+"web")
        top_menu = request.website.menu_id

        homepage = request.website.homepage_id
        if homepage and (homepage.sudo().is_visible or request.env.user.has_group('base.group_user')) and homepage.url != '/':
            return request.env['ir.http'].reroute(homepage.url)

        website_page = request.env['ir.http']._serve_page()
        if website_page:
            return website_page
        else:
            first_menu = top_menu and top_menu.child_id and top_menu.child_id.filtered(lambda menu: menu.is_visible)
            if first_menu and first_menu[0].url not in ('/', '', '#') and (not (first_menu[0].url.startswith(('/?', '/#', ' ')))):
                return request.redirect(first_menu[0].url)

        raise request.not_found()
