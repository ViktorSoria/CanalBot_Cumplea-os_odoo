
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.web import Home
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.website_sale_stock.controllers.main import WebsiteSaleStock
from odoo.tools.translate import _
from odoo.exceptions import ValidationError
import json
import logging

_log = logging.getLogger(__name__)

class WebsiteSaleP(http.Controller):

    # @http.route('/web/healthcheck/', type='http', auth='none',methods=['POST','GET'])
    # def touch_http(self, **kwargs):
    #     return "ok"

    @http.route('/web/healthcheck/', type='json', auth='none')
    def touch_json(self, **kwargs):
        return "ok"