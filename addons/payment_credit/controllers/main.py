# -*- coding: utf-8 -*-
import logging
import pprint
import werkzeug

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class CreditController(http.Controller):
    _accept_url = '/payment/credit/feedback'

    @http.route([
        '/payment/credit/feedback',
    ], type='http', auth='public', csrf=False)
    def credit_form_feedback(self, **post):
        _logger.info('Beginning form_feedback with post data %s', pprint.pformat(post))  # debug
        request.env['payment.transaction'].sudo().form_feedback(post, 'credit')
        return werkzeug.utils.redirect('/payment/process')
