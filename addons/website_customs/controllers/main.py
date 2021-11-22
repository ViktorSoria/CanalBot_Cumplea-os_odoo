
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.web import Home
from odoo.tools.translate import _
import logging

_log = logging.getLogger(__name__)


# class WebsiteBackend(Home):

    # @http.route('/', type='http', auth="public", website=True, sitemap=True)
    # def index(self, **kw):
    #     # prefetch all menus (it will prefetch website.page too)
    #     _log.warning("nuevo controlador")
    #     _log.warning(request.httprequest.url_root)
    #     if "192.168.1.106" not in request.httprequest.url_root:
    #         return request.redirect(request.httprequest.url_root+"web")
    #     top_menu = request.website.menu_id
    #
    #     homepage = request.website.homepage_id
    #     if homepage and (homepage.sudo().is_visible or request.env.user.has_group('base.group_user')) and homepage.url != '/':
    #         return request.env['ir.http'].reroute(homepage.url)
    #
    #     website_page = request.env['ir.http']._serve_page()
    #     if website_page:
    #         return website_page
    #     else:
    #         first_menu = top_menu and top_menu.child_id and top_menu.child_id.filtered(lambda menu: menu.is_visible)
    #         if first_menu and first_menu[0].url not in ('/', '', '#') and (not (first_menu[0].url.startswith(('/?', '/#', ' ')))):
    #             return request.redirect(first_menu[0].url)
    #
    #     raise request.not_found()
