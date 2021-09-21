import odoo
from odoo import http
from odoo import models, fields, api, http, SUPERUSER_ID
from odoo.http import content_disposition, request
from odoo.addons.web.controllers.main import _serialize_exception
from odoo.tools import html_escape
import logging

_logger = logging.getLogger("Moto Control")
import json


class RecibeLinea(http.Controller):

    @http.route('/price_list', type='json', auth='user', methods=['POST'], csrf=False)
    def pricelist(self, **kw):
        _logger.warning("entro")
        data = json.loads(request.httprequest.data)
        datos = data.get('params', {})
        id = datos.get('id')
        lineas = datos.get('lineas')
        if lineas:
            request.env['product.pricelist'].sudo().browse(id).write(lineas)
        else:
            precio = datos.get('precio')
            request.env['product.template'].sudo().browse(id).write({'list_price':precio})
        request.env.cr.commit()
        return True

    @http.route('/image', type='json', auth='user', methods=['POST'], csrf=False)
    def image(self, **kw):
        _logger.warning("entro")
        data = json.loads(request.httprequest.data)
        datos = data.get('params', {})
        id = datos.get('id')
        image = datos.get('image').encode()
        request.env['product.template'].sudo().browse(id).write({'image_1920':image})
        request.env.cr.commit()
        return True