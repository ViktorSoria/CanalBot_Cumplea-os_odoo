# -*- coding: utf-8 -*-

from odoo import api, models, fields, _, SUPERUSER_ID
from odoo.http import request
from datetime import timedelta
import logging

_log = logging.getLogger("Website (%s) -------> " % __name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_id', 'price_unit', 'product_uom', 'product_uom_qty', 'tax_id')
    def _onchange_discount(self):
        if not (self.product_id and self.product_uom and
                self.order_id.partner_id and self.order_id.pricelist_id and
                (self.order_id.pricelist_id.discount_policy == 'without_discount' or self.env.context.get('politica','') == 'without_discount') and
                self.env.user.has_group('product.group_discount_per_so_line')):
            return
        return super(SaleOrderLine,self)._onchange_discount()

    def _get_real_price_currency(self, product, rule_id, qty, uom, pricelist_id):
        """Quitamos listas de precio tipo mostrar descuento"""
        PricelistItem = self.env['product.pricelist.item']
        field_name = 'lst_price'
        currency_id = None
        product_currency = product.currency_id
        if rule_id:
            pricelist_item = PricelistItem.browse(rule_id)
            if self.env.context.get('politica','') == 'without_discount' or pricelist_item.pricelist_id.discount_policy == 'without_discount':
                while pricelist_item.base == 'pricelist' and pricelist_item.base_pricelist_id \
                        and (self.env.context.get('politica','') == 'without_discount' or pricelist_item.base_pricelist_id.discount_policy == 'without_discount'):
                    price, rule_id = pricelist_item.base_pricelist_id.with_context(uom=uom.id).get_product_price_rule(
                        product, qty, self.order_id.partner_id)
                    pricelist_item = PricelistItem.browse(rule_id)

            if pricelist_item.base == 'standard_price':
                field_name = 'standard_price'
                product_currency = product.cost_currency_id
            elif pricelist_item.base == 'pricelist' and pricelist_item.base_pricelist_id:
                field_name = 'price'
                product = product.with_context(pricelist=pricelist_item.base_pricelist_id.id)
                product_currency = pricelist_item.base_pricelist_id.currency_id
            currency_id = pricelist_item.pricelist_id.currency_id

        if not currency_id:
            currency_id = product_currency
            cur_factor = 1.0
        else:
            if currency_id.id == product_currency.id:
                cur_factor = 1.0
            else:
                cur_factor = currency_id._get_conversion_rate(product_currency, currency_id,
                                                              self.company_id or self.env.company,
                                                              self.order_id.date_order or fields.Date.today())

        product_uom = self.env.context.get('uom') or product.uom_id.id
        if uom and uom.id != product_uom:
            # the unit price is in a different uom
            uom_factor = uom._compute_price(1.0, product.uom_id)
        else:
            uom_factor = 1.0

        return product[field_name] * uom_factor * cur_factor, currency_id

    cambiar_precio_unitario = fields.Boolean(string='Modificar precio unitario', compute='PermisoPrecioUnitario', default=False)

    def PermisoPrecioUnitario(self):
        self.cambiar_precio_unitario = self.env.user.has_group('website_customs.group_edit_unit_price')


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def update_prices(self):
        """Quitamos listas de precio tipo mostrar descuento"""
        self.ensure_one()
        lines_to_update = []
        for line in self.order_line.filtered(lambda line: not line.display_type):
            product = line.product_id.with_context(
                partner=self.partner_id,
                quantity=line.product_uom_qty,
                date=self.date_order,
                pricelist=self.pricelist_id.id,
                uom=line.product_uom.id
            )
            price_unit = self.env['account.tax']._fix_tax_included_price_company(
                line._get_display_price(product), line.product_id.taxes_id, line.tax_id, line.company_id)
            if (self.env.context.get('politica','') == 'without_discount' or self.pricelist_id.discount_policy == 'without_discount') and price_unit:
                discount = max(0, (price_unit - product.price) * 100 / price_unit)
            else:
                discount = 0
            lines_to_update.append((1, line.id, {'price_unit': price_unit, 'discount': discount}))
        self.update({'order_line': lines_to_update})
        self.show_update_pricelist = False
        self.message_post(body=_("Product prices have been recomputed according to pricelist <b>%s<b> ",
                                 self.pricelist_id.display_name))
        for line in self.sale_order_option_ids:
            line.price_unit = self.pricelist_id.get_product_price(line.product_id, line.quantity, self.partner_id, uom_id=line.uom_id.id)

    @api.onchange('sale_order_template_id')
    def onchange_sale_order_template_id(self):
        """Quitamos listas de precio tipo mostrar descuento"""
        if not self.sale_order_template_id:
            self.require_signature = self._get_default_require_signature()
            self.require_payment = self._get_default_require_payment()
            return

        template = self.sale_order_template_id.with_context(lang=self.partner_id.lang)

        # --- first, process the list of products from the template
        order_lines = [(5, 0, 0)]
        for line in template.sale_order_template_line_ids:
            data = self._compute_line_data_for_template_change(line)

            if line.product_id:
                price = line.product_id.lst_price
                discount = 0

                if self.pricelist_id:
                    pricelist_price = self.pricelist_id.with_context(uom=line.product_uom_id.id).get_product_price(
                        line.product_id, 1, False)

                    if (self.env.context.get('politica','') == 'without_discount' or self.pricelist_id.discount_policy == 'without_discount') and price:
                        discount = max(0, (price - pricelist_price) * 100 / price)
                    else:
                        price = pricelist_price

                data.update({
                    'price_unit': price,
                    'discount': discount,
                    'product_uom_qty': line.product_uom_qty,
                    'product_id': line.product_id.id,
                    'product_uom': line.product_uom_id.id,
                    'customer_lead': self._get_customer_lead(line.product_id.product_tmpl_id),
                })

            order_lines.append((0, 0, data))

        self.order_line = order_lines
        self.order_line._compute_tax_id()

        # then, process the list of optional products from the template
        option_lines = [(5, 0, 0)]
        for option in template.sale_order_template_option_ids:
            data = self._compute_option_data_for_template_change(option)
            option_lines.append((0, 0, data))

        self.sale_order_option_ids = option_lines

        if template.number_of_days > 0:
            self.validity_date = fields.Date.context_today(self) + timedelta(template.number_of_days)

        self.require_signature = template.require_signature
        self.require_payment = template.require_payment

        if template.note:
            self.note = template.note

    def _compute_option_data_for_template_change(self, option):
        """Quitamos listas de precio tipo mostrar descuento"""
        price = option.product_id.lst_price
        discount = 0

        if self.pricelist_id:
            pricelist_price = self.pricelist_id.with_context(uom=option.uom_id.id).get_product_price(option.product_id,
                                                                                                     1, False)

            if (self.env.context.get('politica','') == 'without_discount' or self.pricelist_id.discount_policy == 'without_discount') and price:
                discount = max(0, (price - pricelist_price) * 100 / price)
            else:
                price = pricelist_price

        return {
            'product_id': option.product_id.id,
            'name': option.name,
            'quantity': option.quantity,
            'uom_id': option.uom_id.id,
            'price_unit': price,
            'discount': discount
        }