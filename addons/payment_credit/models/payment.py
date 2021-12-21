# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.tools.float_utils import float_compare

import logging
import pprint

_logger = logging.getLogger(__name__)


class CreditPaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[
        ('credit', 'Credito')
    ], default='credit', ondelete={'credit': 'set default'})

    @api.model
    def _create_missing_journal_for_acquirers(self, company=None):
        # By default, the wire credit method uses the default Bank journal.
        company = company or self.env.company
        acquirers = self.env['payment.acquirer'].search(
            [('provider', '=', 'credit'), ('journal_id', '=', False), ('company_id', '=', company.id)])

        bank_journal = self.env['account.journal'].search(
            [('type', '=', 'bank'), ('company_id', '=', company.id)], limit=1)
        if bank_journal:
            acquirers.write({'journal_id': bank_journal.id})
        return super(CreditPaymentAcquirer, self)._create_missing_journal_for_acquirers(company=company)

    def credit_get_form_action_url(self):
        return '/payment/credit/feedback'

    def _format_credit_data(self):
        company_id = self.env.company.id
        # filter only bank accounts marked as visible
        journals = self.env['account.journal'].search([('type', '=', 'bank'), ('company_id', '=', company_id)])
        accounts = journals.mapped('bank_account_id').name_get()
        bank_title = _('Bank Accounts') if len(accounts) > 1 else _('Bank Account')
        bank_accounts = ''.join(['<ul>'] + ['<li>%s</li>' % name for id, name in accounts] + ['</ul>'])
        post_msg = _('''<div>
<h3>Please use the following credit details</h3>
<h4>%(bank_title)s</h4>
%(bank_accounts)s
<h4>Communication</h4>
<p>Please use the order name as communication reference.</p>
</div>''') % {
            'bank_title': bank_title,
            'bank_accounts': bank_accounts,
        }
        return post_msg

    @api.model
    def create(self, values):
        """ Hook in create to create a default pending_msg. This is done in create
        to have access to the name and other creation values. If no pending_msg
        or a void pending_msg is given at creation, generate a default one. """
        if values.get('provider') == 'credit' and not values.get('pending_msg'):
            values['pending_msg'] = self._format_credit_data()
        return super(CreditPaymentAcquirer, self).create(values)

    def write(self, values):
        """ Hook in write to create a default pending_msg. See create(). """
        if not values.get('pending_msg', False) and all(not acquirer.pending_msg and acquirer.provider != 'credit' for acquirer in self) and values.get('provider') == 'credit':
            values['pending_msg'] = self._format_credit_data()
        return super(CreditPaymentAcquirer, self).write(values)


class CreditPaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    @api.model
    def _credit_form_get_tx_from_data(self, data):
        reference, amount, currency_name = data.get('reference'), data.get('amount'), data.get('currency_name')
        tx = self.search([('reference', '=', reference)])

        if not tx or len(tx) > 1:
            error_msg = _('received data for reference %s') % (pprint.pformat(reference))
            if not tx:
                error_msg += _('; no order found')
            else:
                error_msg += _('; multiple order found')
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        return tx

    def _credit_form_get_invalid_parameters(self, data):
        invalid_parameters = []

        if float_compare(float(data.get('amount') or '0.0'), self.amount, 2) != 0:
            invalid_parameters.append(('amount', data.get('amount'), '%.2f' % self.amount))
        if data.get('currency') != self.currency_id.name:
            invalid_parameters.append(('currency', data.get('currency'), self.currency_id.name))

        return invalid_parameters

    def _credit_form_validate(self, data):
        _logger.info('Validated credit payment for tx %s: set as pending' % (self.reference))
        # reviser credito
        credit = False
        if len(self.sale_order_ids)==1:
            credit = self.sale_order_ids.check_credit()
        if credit:
            self._set_transaction_done()
        else:
            self._set_transaction_pending()
        return True

    def _create_payment(self, add_payment_vals={}):
        ''' Create an account.payment record for the current payment.transaction.
        If the transaction is linked to some invoices, the reconciliation will be done automatically.
        :param add_payment_vals:    Optional additional values to be passed to the account.payment.create method.
        :return:                    An account.payment record.
        '''
        self.ensure_one()

        payment_vals = {
            'amount': self.amount,
            'payment_type': 'inbound' if self.amount > 0 else 'outbound',
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.commercial_partner_id.id,
            'partner_type': 'customer',
            'journal_id': self.acquirer_id.journal_id.id,
            'company_id': self.acquirer_id.company_id.id,
            'payment_method_id': self.env.ref('payment.account_payment_method_electronic_in').id,
            'payment_token_id': self.payment_token_id and self.payment_token_id.id or None,
            'payment_transaction_id': self.id,
            'ref': self.reference,
            **add_payment_vals,
        }
        payment = self.env['account.payment'].create(payment_vals)
        if self.provider == 'credit':
            self.payment_id = payment
            return payment
        payment.action_post()

        # Track the payment to make a one2one.
        self.payment_id = payment

        if self.invoice_ids:
            self.invoice_ids.filtered(lambda move: move.state == 'draft')._post()

            (payment.line_ids + self.invoice_ids.line_ids)\
                .filtered(lambda line: line.account_id == payment.destination_account_id and not line.reconciled)\
                .reconcile()

        return payment