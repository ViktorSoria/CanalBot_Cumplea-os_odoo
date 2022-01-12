# -*- encoding: utf-8 -*-

import logging
import base64
import requests
import json
from zeep import Client
from zeep.transports import Transport
from odoo import api, models, fields, tools, _

_logger = logging.getLogger("Pasarela tekniu: ")


class Partner(models.Model):
    _inherit = "res.partner"

    country_id = fields.Many2one(default=lambda self: self.env.ref('base.mx').id)

    def l10n_mx_edi_get_customer_rfc(self,vat=False):
        if not vat:
            vat = self.vat
        if len(vat) > 13:
            vat = vat[2:]
        return vat


class ResCompany(models.Model):
    _inherit = 'res.company'

    l10n_mx_edi_pac = fields.Selection(selection_add=[('tekniu', 'Soluciones en Ingeniería Tekniu')],default='tekniu')


class AccountEdiFormat(models.Model):
    _inherit = 'account.edi.format'

    def _l10n_mx_edi_get_common_cfdi_values(self, move):
        res = super()._l10n_mx_edi_get_common_cfdi_values(move)
        res['customer_rfc'] = self.env['res.partner'].l10n_mx_edi_get_customer_rfc(res['customer_rfc'])
        return res

    def _l10n_mx_edi_get_tekniu_credentials(self, move):
        """Extrae las credenciales de la compañia"""
        test = move.company_id.l10n_mx_edi_pac_test_env
        username = move.company_id.l10n_mx_edi_pac_username
        password = move.company_id.l10n_mx_edi_pac_password
        url = 'https://facturacion.tekniu.mx/facturacion_gw'
        if not username or not password:
            return {
                'errors': [_("The username and/or password are missing.")]
            }
        return {
            'username': username,
            'password': password,
            'sign_url': url,
            'cancel_url': url,
            'test': test
        }

    def _l10n_mx_edi_tekniu_sign(self,move,credentials,cfdi):
        """Envio a la pasarela de tekniu (pagos y facturas)"""
        url = credentials['sign_url']
        pre_xml = cfdi.decode('utf-8')
        json_invoice = {
            'Cliente': {'Usuario': credentials['username'], 'Password': credentials['password']},
            'Service': 'Timbrar',
            'Type': 'xml',
            'Xml': pre_xml,
            'Prueba': credentials['test']
        }
        try:
            response = requests.post(url,auth=None, verify=False, data=json.dumps({'params':json_invoice}),headers={"Content-type": "application/json"})
        except Exception as e:
            return {'errors': [str(e)]}
        result = response.json().get('result',{})
        code = result.get('code','')
        msg = result.get('description','')
        errors = []
        if code or msg:
            errors.append(_("Code : %s") % code)
            errors.append(_("Message : %s") % msg)
            return {'errors': errors}
        xml_signed = result.get('xml', None)
        _logger.warning(xml_signed)

        # Check if response xml is base64 encoded.
        # Check if is str and not bytes.
        if isinstance(xml_signed, str):
            xml_signed = xml_signed.encode('UTF-8'),
        if xml_signed.decode('UTF-8').find('<?xml version=') >= 0 and xml_signed.decode('UTF-8').find(
                'encoding=') >= 0:
            xml_signed = base64.encodebytes(xml_signed)
        else:
            b64_cfdi = xml_signed
            while True:
                try:
                    va = base64.decodebytes(b64_cfdi)
                    if va.decode('UTF-8').find('<?xml version=') >= 0 and va.decode('UTF-8').find('encoding=') >= 0:
                        xml_signed = b64_cfdi
                        break
                    else:
                        b64_cfdi = va
                except Exception:
                    _logger.warning(" CFDI no pudo ser entendido por el sistema.")
        return {
            'cfdi_signed': xml_signed,
            'cfdi_encoding': 'base64',
        }

    def _l10n_mx_edi_tekniu_sign_invoice(self, invoice, credentials, cfdi):
        return self._l10n_mx_edi_tekniu_sign(invoice, credentials, cfdi)

    def _l10n_mx_edi_tekniu_sign_payment(self, move, credentials, cfdi):
        return self._l10n_mx_edi_tekniu_sign(move, credentials, cfdi)

    def _l10n_mx_edi_tekniu_cancel_invoice(self, invoice, credentials, cfdi):
        return self._l10n_mx_edi_tekniu_cancel(invoice, credentials, cfdi)

    def _l10n_mx_edi_tekniu_cancel_payment(self, move, credentials, cfdi):
        return self._l10n_mx_edi_tekniu_cancel(move, credentials, cfdi)

    def _l10n_mx_edi_tekniu_cancel(self,move,credentials,cfdi):
        """CANCEL for Tekniu."""
        url = credentials['cancel_url']
        json_invoice = {
            'Cliente': {'Usuario': credentials['username'], 'Password': credentials['password']},
            'Service': 'Cancelar',
            'Prueba': credentials['test'],
            'rfc': move.company_id.partner_id.l10n_mx_edi_get_customer_rfc(),
            'Uuid': move.l10n_mx_edi_cfdi_uuid,
            'Pass_pfx': '',
            'pfx_b64': '',
            'generate_pfx': True,
        }
        try:
            response = requests.post(url,auth=None, verify=False, data=json.dumps({'params':json_invoice}),headers={"Content-type": "application/json"})
        except Exception as e:
            return {'errors': [str(e)]}
        result = response.json().get('result',{})
        _logger.warning(result)
        validate = result.get('validate',False)
        code = result.get('code','')
        msg = result.get('description','')
        errors = []
        if not validate:
            errors.append(_("Code : %s") % code)
            errors.append(_("Message : %s") % msg)
            _logger.warning(errors)
            return {'errors': errors}
        return {'success': True}