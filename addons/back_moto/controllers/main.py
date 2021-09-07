# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import odoo
from odoo import http
from odoo import models, fields, api, http, SUPERUSER_ID
from odoo.http import content_disposition, request
from odoo.addons.web.controllers.main import _serialize_exception
from odoo.tools import html_escape

import json


class RecibeLinea(http.Controller):

    @http.route('/price_list', type='json', auth=False, methods=['POST'], csrf=False)
    def pricelist(self, **kw):
        data = json.loads(request.httprequest.data)
        headers = request.httprequest.headers
        db = headers.get('db') if 'db' in headers else False
        registry = odoo.registry(db) if db else odoo.registry()
        cr = registry.cursor()
        env = odoo.api.Environment(cr, SUPERUSER_ID, {})
        datos = data.get('params', {})
        id = datos.get('id')
        lineas = datos.get('lineas')
        env['product.pricelist'].sudo().browse(id).write(lineas)
        env.cr.commit()
        return {'recibe':True}