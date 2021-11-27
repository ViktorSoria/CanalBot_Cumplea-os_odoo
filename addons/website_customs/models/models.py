# -*- coding: utf-8 -*-

from odoo import api, models, fields, _, SUPERUSER_ID
from odoo.http import request
from datetime import timedelta
import logging

_log = logging.getLogger("Website (%s) -------> " % __name__)


class Location(models.Model):
    _inherit = "stock.location"

    dis_website = fields.Boolean("Disponible en sitio web",default=True)
    name_almacen = fields.Char("Nombre Almacen")
    promocion = fields.Boolean("Promocion")
    remate = fields.Boolean("Remate")


class Website(models.Model):
    _inherit = "website"

    def get_current_pricelist(self):
        available_pricelists = self.get_pricelist_available()
        pl = None
        partner = self.env.user.partner_id
        if request and request.session.get('website_sale_current_pl'):
            pl = self.env['product.pricelist'].browse(request.session['website_sale_current_pl'])
            if pl not in available_pricelists:
                pl = None
                request.session.pop('website_sale_current_pl')
        if not pl:
            pl = partner.last_website_so_id.pricelist_id
            if not pl:
                pl = partner.property_product_pricelist
            if available_pricelists and pl not in available_pricelists:
                pl = available_pricelists[0]
        pl = self.env['product.pricelist'].search([('relational_list', '=', pl.id)]) or pl
        if not pl:
            _log.error('Fail to find pricelist for partner "%s" (id %s)', partner.name, partner.id)
        return pl

    def sale_get_order(self, force_create=False, code=None, update_pricelist=False, force_pricelist=False):
        """ Return the current sales order after mofications specified by params.
        :param bool force_create: Create sales order if not already existing
        :param str code: Code to force a pricelist (promo code)
                         If empty, it's a special case to reset the pricelist with the first available else the default.
        :param bool update_pricelist: Force to recompute all the lines from sales order to adapt the price with the current pricelist.
        :param int force_pricelist: pricelist_id - if set,  we change the pricelist with this one
        :returns: browse record for the current sales order
        """
        self.ensure_one()
        partner = self.env.user.partner_id
        sale_order_id = request.session.get('sale_order_id')
        check_fpos = False
        if not sale_order_id and not self.env.user._is_public():
            last_order = partner.last_website_so_id
            if last_order:
                available_pricelists = self.get_pricelist_available()
                # Do not reload the cart of this user last visit if the cart uses a pricelist no longer available.
                sale_order_id = last_order.pricelist_id in available_pricelists and last_order.id
                check_fpos = True

        # Test validity of the sale_order_id
        sale_order = self.env['sale.order'].with_company(request.website.company_id.id).sudo().browse(sale_order_id).exists() if sale_order_id else None

        # Do not reload the cart of this user last visit if the Fiscal Position has changed.
        if check_fpos and sale_order:
            fpos_id = (
                self.env['account.fiscal.position'].sudo()
                .with_company(sale_order.company_id.id)
                .get_fiscal_position(sale_order.partner_id.id, delivery_id=sale_order.partner_shipping_id.id)
            ).id
            if sale_order.fiscal_position_id.id != fpos_id:
                sale_order = None

        if not (sale_order or force_create or code):
            if request.session.get('sale_order_id'):
                request.session['sale_order_id'] = None
            return self.env['sale.order']

        if self.env['product.pricelist'].browse(force_pricelist).exists():
            pricelist_id = force_pricelist
            _log.warning("lista forzada")
            _log.warning(pricelist_id)
            request.session['website_sale_current_pl'] = pricelist_id
            update_pricelist = True
        else:
            pricelist_id = request.session.get('website_sale_current_pl') or self.get_current_pricelist().id

        if not self._context.get('pricelist'):
            self = self.with_context(pricelist=pricelist_id)

        # cart creation was requested (either explicitly or to configure a promo code)
        if not sale_order:
            # TODO cache partner_id session
            pricelist = self.env['product.pricelist'].browse(pricelist_id).sudo()
            pricelist_rel = pricelist.relational_list or pricelist
            so_data = self._prepare_sale_order_values(partner, pricelist_rel)
            sale_order = self.env['sale.order'].with_company(request.website.company_id.id).with_user(SUPERUSER_ID).create(so_data)

            # set fiscal position
            if request.website.partner_id.id != partner.id:
                sale_order.onchange_partner_shipping_id()
            else: # For public user, fiscal position based on geolocation
                country_code = request.session['geoip'].get('country_code')
                if country_code:
                    country_id = request.env['res.country'].search([('code', '=', country_code)], limit=1).id
                    sale_order.fiscal_position_id = request.env['account.fiscal.position'].sudo().with_company(request.website.company_id.id)._get_fpos_by_region(country_id)
                else:
                    # if no geolocation, use the public user fp
                    sale_order.onchange_partner_shipping_id()

            request.session['sale_order_id'] = sale_order.id

        # case when user emptied the cart
        if not request.session.get('sale_order_id'):
            request.session['sale_order_id'] = sale_order.id

        # check for change of pricelist with a coupon
        pricelist_id = pricelist_id or partner.property_product_pricelist.id
        _log.warning("lista partner")
        _log.warning(pricelist_id)
        # check for change of partner_id ie after signup
        if sale_order.partner_id.id != partner.id and request.website.partner_id.id != partner.id:
            flag_pricelist = False
            if pricelist_id != sale_order.pricelist_id.id:
                _log.warning("listas orden diferente 1")
                _log.warning(pricelist_id)
                flag_pricelist = True
            fiscal_position = sale_order.fiscal_position_id.id

            # change the partner, and trigger the onchange
            sale_order.write({'partner_id': partner.id})
            sale_order.with_context(not_self_saleperson=True).onchange_partner_id()
            sale_order.write({'partner_invoice_id': partner.id})
            sale_order.onchange_partner_shipping_id() # fiscal position
            sale_order['payment_term_id'] = self.sale_get_payment_term(partner)

            # check the pricelist : update it if the pricelist is not the 'forced' one
            values = {}
            if sale_order.pricelist_id:
                if sale_order.pricelist_id.id != pricelist_id:
                    _log.warning("listas orden diferente 2")
                    _log.warning(pricelist_id)
                    _log.warning(sale_order.pricelist_id.id)
                    values['pricelist_id'] = pricelist_id
                    update_pricelist = True

            # if fiscal position, update the order lines taxes
            if sale_order.fiscal_position_id:
                sale_order._compute_tax_id()

            # if values, then make the SO update
            if values:
                sale_order.write(values)

            # check if the fiscal position has changed with the partner_id update
            recent_fiscal_position = sale_order.fiscal_position_id.id
            # when buying a free product with public user and trying to log in, SO state is not draft
            if (flag_pricelist or recent_fiscal_position != fiscal_position) and sale_order.state == 'draft':
                update_pricelist = True

        if code and code != sale_order.pricelist_id.code:
            code_pricelist = self.env['product.pricelist'].sudo().search([('code', '=', code)], limit=1)
            if code_pricelist:
                pricelist_id = code_pricelist.id
                update_pricelist = True
        elif code is not None and sale_order.pricelist_id.code and code != sale_order.pricelist_id.code:
            # code is not None when user removes code and click on "Apply"
            pricelist_id = partner.property_product_pricelist.id
            update_pricelist = True

        # update the pricelist
        if update_pricelist:
            _log.warning("actualizando sesion y carrito")
            _log.warning(pricelist_id)
            request.session['website_sale_current_pl'] = pricelist_id
            pricelist = self.env['product.pricelist'].browse(pricelist_id).sudo()
            values = {'pricelist_id': pricelist.relational_list.id or pricelist_id}
            sale_order.write(values)
            for line in sale_order.order_line:
                if line.exists():
                    sale_order._cart_update(product_id=line.product_id.id, line_id=line.id, add_qty=0)

        return sale_order


class List(models.Model):
    _inherit = "product.pricelist"

    relational_list = fields.Many2one("product.pricelist",'Lista relacionada')
    por_promo = fields.Float('Porcentaje promocion')
    por_remate = fields.Float('Porcentaje remate')
    promocion = fields.Boolean("Promocion y remate")


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('product_id.display_name')
    def _compute_name_short(self):
        for record in self:
            record.name_short = record.product_id.display_name

    @api.onchange('product_id', 'price_unit', 'product_uom', 'product_uom_qty', 'tax_id')
    def _onchange_discount(self):
        """Quitamos listas de precio tipo mostrar descuento"""
        return

    def _get_real_price_currency(self, product, rule_id, qty, uom, pricelist_id):
        """Quitamos listas de precio tipo mostrar descuento"""
        PricelistItem = self.env['product.pricelist.item']
        field_name = 'lst_price'
        currency_id = None
        product_currency = product.currency_id
        if rule_id:
            pricelist_item = PricelistItem.browse(rule_id)
            # if pricelist_item.pricelist_id.discount_policy == 'without_discount':
            #     while pricelist_item.base == 'pricelist' and pricelist_item.base_pricelist_id and pricelist_item.base_pricelist_id.discount_policy == 'without_discount':
            #         price, rule_id = pricelist_item.base_pricelist_id.with_context(uom=uom.id).get_product_price_rule(product, qty, self.order_id.partner_id)
            #         pricelist_item = PricelistItem.browse(rule_id)
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
                cur_factor = currency_id._get_conversion_rate(product_currency, currency_id, self.company_id or self.env.company, self.order_id.date_order or fields.Date.today())

        product_uom = self.env.context.get('uom') or product.uom_id.id
        if uom and uom.id != product_uom:
            # the unit price is in a different uom
            uom_factor = uom._compute_price(1.0, product.uom_id)
        else:
            uom_factor = 1.0

        return product[field_name] * uom_factor * cur_factor, currency_id


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _cart_update(self, product_id=None, line_id=None, add_qty=0, set_qty=0, **kwargs):
        obj = self.with_context(no_ware=True)
        return super(SaleOrder, obj)._cart_update(product_id, line_id, add_qty, set_qty, **kwargs)

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
            discount = 0
            lines_to_update.append((1, line.id, {'price_unit': price_unit, 'discount': discount}))
        self.update({'order_line': lines_to_update})
        self.show_update_pricelist = False
        self.message_post(body=_("Product prices have been recomputed according to pricelist <b>%s<b> ", self.pricelist_id.display_name))

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
                    pricelist_price = self.pricelist_id.with_context(uom=line.product_uom_id.id).get_product_price(line.product_id, 1, False)
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
            pricelist_price = self.pricelist_id.with_context(uom=option.uom_id.id).get_product_price(option.product_id, 1, False)
            price = pricelist_price

        return {
            'product_id': option.product_id.id,
            'name': option.name,
            'quantity': option.quantity,
            'uom_id': option.uom_id.id,
            'price_unit': price,
            'discount': discount
        }

    def _website_product_id_change(self, order_id, product_id, qty=0):
        order = self.sudo().browse(order_id)
        product_context = dict(self.env.context)
        product_context.setdefault('lang', order.partner_id.lang)
        product_context.update({
            'partner': order.partner_id,
            'quantity': qty,
            'date': order.date_order,
            'pricelist': order.pricelist_id.id,
        })
        product = self.env['product.product'].with_context(product_context).with_company(order.company_id.id).browse(product_id)
        discount = 0
        pu = product.price
        if order.pricelist_id and order.partner_id:
            order_line = order._cart_find_product_line(product.id)
            if order_line:
                pu = self.env['account.tax']._fix_tax_included_price_company(pu, product.taxes_id, order_line[0].tax_id, self.company_id)

        return {
            'product_id': product_id,
            'product_uom_qty': qty,
            'order_id': order_id,
            'product_uom': product.uom_id.id,
            'price_unit': pu,
            'discount': discount,
        }


class Product(models.Model):
    _inherit = "product.product"

    def _compute_quantities_dict(self, lot_id, owner_id, package_id, from_date=False, to_date=False):
        obj = self
        if self.env.context.get('no_ware'):
            ware = self.env['stock.warehouse'].sudo().search([]).ids
            obj = self.with_context(warehouse=ware)
        return super(Product,obj)._compute_quantities_dict(lot_id=lot_id, owner_id=owner_id, package_id=package_id, from_date=from_date, to_date=to_date)

    def available_qty(self,location=False):
        if not location:
            location = self.env['stock.location'].sudo().search([('usage','=','internal')])
        else:
            location = self.env['stock.location'].sudo().browse(location)
        quants = self.env['stock.quant'].sudo()
        for l in location:
            quants += self.env['stock.quant'].sudo()._gather(self, l)
        ware = self.env['stock.warehouse'].sudo().search([])
        ware = {w.lot_stock_id.id:w.name for w in ware}
        exis = [("%s"%ware.get(q.location_id.id,q.location_id.display_name), q.available_quantity) for q in quants]
        return exis

    def price_compute(self, price_type, uom=False, currency=False, company=None):
        # TDE FIXME: delegate to template or not ? fields are reencoded here ...
        # compatibility about context keys used a bit everywhere in the code
        if not uom and self._context.get('uom'):
            uom = self.env['uom.uom'].browse(self._context['uom'])
        if not currency and self._context.get('currency'):
            currency = self.env['res.currency'].browse(self._context['currency'])

        products = self
        if price_type == 'standard_price':
            # standard_price field can only be seen by users in base.group_user
            # Thus, in order to compute the sale price from the cost for users not in this group
            # We fetch the standard price as the superuser
            products = self.with_company(company or self.env.company).sudo()
        lista = self._context.get('pricelist_id')
        items_dic = {}
        if lista:
            items = self.env['product.pricelist.item'].search([('product_tmpl_id', 'in', products.mapped('product_tmpl_id').ids), ('pricelist_id', '=', lista.id)])
            items_dic = {i.product_tmpl_id.id: i.fixed_price for i in items}
        prices = dict.fromkeys(self.ids, 0.0)
        for product in products:
            prices[product.id] = items_dic.get(product.product_tmpl_id.id,0) or product[price_type] or 0.0
            if price_type == 'list_price':
                prices[product.id] += product.price_extra
                # we need to add the price from the attributes that do not generate variants
                # (see field product.attribute create_variant)
                if self._context.get('no_variant_attributes_price_extra'):
                    # we have a list of price_extra that comes from the attribute values, we need to sum all that
                    prices[product.id] += sum(self._context.get('no_variant_attributes_price_extra'))

            if uom:
                prices[product.id] = product.uom_id._compute_price(prices[product.id], uom)

            # Convert from current user company currency to asked one
            # This is right cause a field cannot be in more than one currency
            if currency:
                prices[product.id] = product.currency_id._convert(
                    prices[product.id], currency, product.company_id, fields.Date.today())

        return prices


class Template(models.Model):
    _inherit = "product.template"

    vendido = fields.Boolean("Mas vendido")
    nuevo = fields.Boolean("Mas nuevo")

    @api.model
    def product_update_fields(self):
        """Hacemos las actualizaciones necesarias para el sitio web
           *secuencia *lo mas nuevo *lo mas vendido *promocion *remate"""
        ##Buscar productos
        nuevo = self.env['product.template'].search([('is_published','=',True)],order="create_date desc",limit=50)
        vendido = self.env['product.product'].search([('list_price','>',10)])
        vendido = vendido.sorted('sales_count',True)[:300]
        vendido = vendido.mapped('product_tmpl_id')
        query = """select p.product_tmpl_id from stock_quant as s 
                inner join stock_location as l on s.location_id = l.id inner join product_product as p on s.product_id = p.id 
                where l.promocion = true and s.quantity-s.reserved_quantity>0;"""
        self.env.cr.execute(query)
        promocion = self._cr.fetchall()
        query = """select p.product_tmpl_id from stock_quant as s 
                        inner join stock_location as l on s.location_id = l.id inner join product_product as p on s.product_id = p.id 
                        where l.remate = true and s.quantity-s.reserved_quantity>0;"""
        self.env.cr.execute(query)
        remate = self._cr.fetchall()
        query = "update product_template set nuevo=false,vendido=false,website_ribbon_id=null;"
        self.env.cr.execute(query)
        self.env.cr.commit()
        ##Actualizar productos
        nuevo.write({'nuevo':True})
        vendido.write({'vendido':True})
        promocion_obj = self.env['product.template'].search([('id', 'in', promocion)])
        remate_obj = self.env['product.template'].search([('id', 'in', remate)])
        promocion_obj.write({'website_ribbon_id':self.env.ref('website_customs.ribbon_15')})
        remate_obj.write({'website_ribbon_id':self.env.ref('website_customs.ribbon_26')})
        ##Ajustar listas de precio
        listas = self.env['product.pricelist'].search([('relational_list','!=',False)])
        data_promo = listas._compute_price_rule_multi([(p,False,False) for p in promocion_obj])
        data_rema = listas._compute_price_rule_multi([(p,False,False) for p in remate_obj])
        for l in listas.filtered(lambda l: l.relational_list.promocion):
            lista_rel = l.relational_list
            lista_rel.mapped('item_ids').filtered(lambda l: l.fixed_price).unlink()
            for p in remate:
                data = {
                    'applied_on': '1_product',
                    'product_tmpl_id': p[0],
                    'compute_price': 'fixed',
                    'fixed_price': data_rema.get(p[0],{}).get(l.id)[0]*(100-lista_rel.por_remate)/100,
                    'pricelist_id': lista_rel.id
                }
                self.env['product.pricelist.item'].create(data)
            for p in promocion:
                data = {
                    'applied_on': '1_product',
                    'product_tmpl_id': p[0],
                    'compute_price': 'fixed',
                    'fixed_price': data_promo.get(p[0],{}).get(l.id)[0]*(100-lista_rel.por_promo)/ 100,
                    'pricelist_id':lista_rel.id
                }
                self.env['product.pricelist.item'].create(data)

    def _get_combination_info(self, combination=False, product_id=False, add_qty=1, pricelist=False, parent_combination=False, only_template=False):
        website_sale_stock_get_quantity = self.env.context.get('website_sale_stock_get_quantity')
        obj = self.with_context(website_sale_stock_get_quantity=False)
        if self.env.context.get('website_id'):
            current_website = self.env['website'].get_current_website()
            if not pricelist:
                pricelist = current_website.get_current_pricelist()
            obj = obj.with_context(pricelist_id=pricelist.relational_list)
        combi = super(Template,obj)._get_combination_info(
            combination=combination, product_id=product_id, add_qty=add_qty, pricelist=pricelist,
            parent_combination=parent_combination, only_template=only_template)
        list_price = combi.get('price')
        price = combi.get('list_price')
        has_discounted_price = pricelist.currency_id.compare_amounts(list_price, price) == 1
        combi.update(
            price=price if has_discounted_price else list_price,
            list_price=list_price,
            has_discounted_price=has_discounted_price,
        )
        if website_sale_stock_get_quantity:
            if combi['product_id']:
                product = self.env['product.product'].sudo().browse(combi['product_id'])
                ware = self.env['stock.warehouse'].sudo().search([]).ids
                virtual_available = product.with_context(warehouse=ware).virtual_available
                combi.update({
                    'virtual_available': virtual_available,
                    'virtual_available_formatted': self.env['ir.qweb.field.float'].value_to_html(virtual_available, {'precision': 0}),
                    'product_type': product.type,
                    'inventory_availability': product.inventory_availability,
                    'available_threshold': product.available_threshold,
                    'custom_message': product.custom_message,
                    'product_template': product.product_tmpl_id.id,
                    'cart_qty': product.cart_qty,
                    'uom_name': product.uom_id.name,
                })
            else:
                product_template = self.sudo()
                combi.update({
                    'virtual_available': 0,
                    'product_type': product_template.type,
                    'inventory_availability': product_template.inventory_availability,
                    'available_threshold': product_template.available_threshold,
                    'custom_message': product_template.custom_message,
                    'product_template': product_template.id,
                    'cart_qty': 0
                })
        return combi

    def price_compute(self, price_type, uom=False, currency=False, company=None):
        # TDE FIXME: delegate to template or not ? fields are reencoded here ...
        # compatibility about context keys used a bit everywhere in the code
        if not uom and self._context.get('uom'):
            uom = self.env['uom.uom'].browse(self._context['uom'])
        if not currency and self._context.get('currency'):
            currency = self.env['res.currency'].browse(self._context['currency'])

        templates = self
        if price_type == 'standard_price':
            # standard_price field can only be seen by users in base.group_user
            # Thus, in order to compute the sale price from the cost for users not in this group
            # We fetch the standard price as the superuser
            templates = self.with_company(company).sudo()
        if not company:
            company = self.env.company
        date = self.env.context.get('date') or fields.Date.today()
        lista = self._context.get('pricelist_id')
        items_dic = {}
        if lista:
            items = self.env['product.pricelist.item'].search([('product_tmpl_id', 'in', templates.ids), ('pricelist_id', '=', lista.id)])
            items_dic = {i.product_tmpl_id.id: i.fixed_price for i in items}
        prices = dict.fromkeys(self.ids, 0.0)
        for template in templates:
            if price_type == 'list_price':
                prices[template.id] = items_dic.get(template.id,0) or template[price_type] or 0.0
            else:
                prices[template.id] = template[price_type] or 0.0
            # yes, there can be attribute values for product template if it's not a variant YET
            # (see field product.attribute create_variant)
            if price_type == 'list_price' and self._context.get('current_attributes_price_extra'):
                # we have a list of price_extra that comes from the attribute values, we need to sum all that
                prices[template.id] += sum(self._context.get('current_attributes_price_extra'))

            if uom:
                prices[template.id] = template.uom_id._compute_price(prices[template.id], uom)

            # Convert from current user company currency to asked one
            # This is right cause a field cannot be in more than one currency
            if currency:
                prices[template.id] = template.currency_id._convert(prices[template.id], currency, company, date)
        return prices