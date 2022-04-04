# -*- coding: utf-8 -*-

from . import controllers
from . import models
from odoo.addons.payment_conekta_oxoo.models.payment_acquirer import create_missing_journal_for_conekta_acquirers
from odoo.addons.payment import reset_payment_provider

def uninstall_hook(cr, registry):
    reset_payment_provider(cr, registry, 'conekta')
    reset_payment_provider(cr, registry, 'conekta_oxxo')
    reset_payment_provider(cr, registry, 'conekta_spei')