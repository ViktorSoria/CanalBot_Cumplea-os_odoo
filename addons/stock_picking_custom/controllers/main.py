import odoo
from odoo import http
from odoo import models, fields, api, http, SUPERUSER_ID
from odoo.http import content_disposition, request
from odoo.addons.web.controllers.main import serialize_exception,content_disposition
import base64
from odoo.tools import html_escape
import logging

_logger = logging.getLogger("Moto Control")


class Binary(http.Controller):

    @http.route('/web/binary/download_document', type='http', auth="public")
    @serialize_exception
    def download_document(self,model,field,id,filename=None, **kw):
         Model = request.env['wizard.download.data']
         res = Model.sudo().browse([int(id)])[0]
         filecontent = base64.b64decode(res.excel_file or '')
         if not filecontent:
             return request.not_found()
         else:
             if not filename:
                 filename = '%s_%s' % (model.replace('.', '_'), id)
             return request.make_response(filecontent, [('Content-Type', 'application/octet-stream'),
                                                        ('Content-Disposition', content_disposition(filename))])