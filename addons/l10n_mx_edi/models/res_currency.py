# coding: utf-8


from odoo import fields, models


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    l10n_mx_edi_decimal_places = fields.Integer(
        'Number of decimals', readonly=True,
        help='Number of decimals to be supported for this currency, according '
        'to the SAT. It will be used in the CFDI to format amounts.')
