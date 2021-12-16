# -*- coding: utf-8 -*-

from odoo import api, models, fields, _, SUPERUSER_ID
from odoo.http import request
from datetime import timedelta
import logging

_log = logging.getLogger("Website (%s) -------> " % __name__)


class Visitor(models.Model):
    _inherit = "website.visitor"

    public_email = fields.Char("Correo envio publicidad")


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
        # check for change of partner_id ie after signup
        if sale_order.partner_id.id != partner.id and request.website.partner_id.id != partner.id:
            flag_pricelist = False
            if pricelist_id != sale_order.pricelist_id.id:
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


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _cart_update(self, product_id=None, line_id=None, add_qty=0, set_qty=0, **kwargs):
        obj = self.with_context(no_ware=True)
        return super(SaleOrder, obj)._cart_update(product_id, line_id, add_qty, set_qty, **kwargs)

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
            items = self.env['product.pricelist.item'].search([('product_tmpl_id', 'in', products.mapped('product_tmpl_id').ids), ('pricelist_id', '=', lista)])
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

    @api.depends_context('pricelist', 'partner', 'quantity', 'uom', 'date', 'no_variant_attributes_price_extra')
    def _compute_product_price(self):
        prices = {}
        pricelist_id_or_name = self._context.get('pricelist')
        if pricelist_id_or_name:
            pricelist = None
            partner = self.env.context.get('partner', False)
            quantity = self.env.context.get('quantity', 1.0)

            # Support context pricelists specified as list, display_name or ID for compatibility
            if isinstance(pricelist_id_or_name, list):
                pricelist_id_or_name = pricelist_id_or_name[0]
            if isinstance(pricelist_id_or_name, str):
                pricelist_name_search = self.env['product.pricelist'].name_search(pricelist_id_or_name, operator='=', limit=1)
                if pricelist_name_search:
                    pricelist = self.env['product.pricelist'].browse([pricelist_name_search[0][0]])
            elif isinstance(pricelist_id_or_name, int):
                pricelist = self.env['product.pricelist'].browse(pricelist_id_or_name)

            if pricelist:
                quantities = [quantity] * len(self)
                partners = [partner] * len(self)
                prices = pricelist.get_products_price(self.with_context(pricelist_id=pricelist.id), quantities, partners)

        for product in self:
            product.price = prices.get(product.id, 0.0)


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
        todos = self.env['product.template'].search([])
        todos._compute_quantities()
        for p in todos:
            p.write({'is_published': p.sale_ok, 'website_sequence': 100000 - p.qty_available - (10000 if p.image_1920 else 0)})
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
        # if lista and not self._context.get('pricelist'):
        if lista:
            items = self.env['product.pricelist.item'].search([('product_tmpl_id', 'in', templates.ids), ('pricelist_id', '=', lista)])
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

    def _compute_template_price_no_inverse(self):
        """The _compute_template_price writes the 'list_price' field with an inverse method
        This method allows computing the price without writing the 'list_price'
        """
        prices = {}
        pricelist_id_or_name = self._context.get('pricelist')
        if pricelist_id_or_name:
            pricelist = None
            partner = self.env.context.get('partner')
            quantity = self.env.context.get('quantity', 1.0)

            # Support context pricelists specified as list, display_name or ID for compatibility
            if isinstance(pricelist_id_or_name, list):
                pricelist_id_or_name = pricelist_id_or_name[0]
            if isinstance(pricelist_id_or_name, str):
                pricelist_data = self.env['product.pricelist'].name_search(pricelist_id_or_name, operator='=', limit=1)
                if pricelist_data:
                    pricelist = self.env['product.pricelist'].browse(pricelist_data[0][0])
            elif isinstance(pricelist_id_or_name, int):
                pricelist = self.env['product.pricelist'].browse(pricelist_id_or_name)

            if pricelist:
                quantities = [quantity] * len(self)
                partners = [partner] * len(self)
                prices = pricelist.get_products_price(self.with_context(pricelist_id=pricelist.id), quantities, partners)

        return prices
    
    def _get_combination_info(self, combination=False, product_id=False, add_qty=1, pricelist=False, parent_combination=False, only_template=False):
        self.ensure_one()
        obj = self.with_context(website_sale_stock_get_quantity=False)
        current_website = False
        if self.env.context.get('website_id'):
            current_website = self.env['website'].get_current_website()
            if not pricelist:
                pricelist = current_website.get_current_pricelist()
            obj = obj.with_context(pricelist_id=pricelist.relational_list.id,politica='without_discount')
        combination_info = obj.ori_get_combination_info(
            combination=combination, product_id=product_id, add_qty=add_qty, pricelist=pricelist,
            parent_combination=parent_combination, only_template=only_template)

        """website"""
        if current_website:
            partner = self.env.user.partner_id
            company_id = current_website.company_id
            product = self.env['product.product'].browse(combination_info['product_id']) or self
            product = product.with_context(politica='without_discount')
            tax_display = self.user_has_groups('account.group_show_line_subtotals_tax_excluded') and 'total_excluded' or 'total_included'
            fpos = self.env['account.fiscal.position'].get_fiscal_position(partner.id).sudo().with_context(politica='without_discount')
            taxes = fpos.map_tax(product.sudo().taxes_id.filtered(lambda x: x.company_id == company_id), product, partner)
            taxes = taxes.with_context(politica='without_discount')
            # The list_price is always the price of one.
            quantity_1 = 1
            combination_info['price'] = self.env['account.tax'].with_context(politica='without_discount')._fix_tax_included_price_company(combination_info['price'], product.sudo().taxes_id, taxes, company_id)
            price = taxes.compute_all(combination_info['price'], pricelist.currency_id, quantity_1, product, partner)[tax_display]
            combination_info['list_price'] = self.env['account.tax'].with_context(politica='without_discount')._fix_tax_included_price_company(combination_info['list_price'], product.sudo().taxes_id, taxes, company_id)
            list_price = taxes.compute_all(combination_info['list_price'], pricelist.currency_id, quantity_1, product, partner)[tax_display]
            has_discounted_price = pricelist.currency_id.compare_amounts(list_price, price) == 1

            combination_info.update(
                price=price,
                list_price=list_price,
                has_discounted_price=has_discounted_price,
            )
        list_price = combination_info.get('price')
        price = combination_info.get('list_price')
        has_discounted_price = pricelist.currency_id.compare_amounts(list_price, price) == 1
        combination_info.update(
            price=price if has_discounted_price else list_price,
            list_price=list_price,
            has_discounted_price=has_discounted_price,
        )
        """website stock"""
        if self.env.context.get('website_sale_stock_get_quantity'):
            if combination_info['product_id']:
                product = self.env['product.product'].sudo().browse(combination_info['product_id'])
                ware = self.env['stock.warehouse'].sudo().search([]).ids
                virtual_available = product.with_context(warehouse=ware).virtual_available
                combination_info.update({
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
                combination_info.update({
                    'virtual_available': 0,
                    'product_type': product_template.type,
                    'inventory_availability': product_template.inventory_availability,
                    'available_threshold': product_template.available_threshold,
                    'custom_message': product_template.custom_message,
                    'product_template': product_template.id,
                    'cart_qty': 0
                })
        return combination_info
    
    def ori_get_combination_info(self, combination=False, product_id=False, add_qty=1, pricelist=False, parent_combination=False, only_template=False):

        self.ensure_one()
        # get the name before the change of context to benefit from prefetch
        display_name = self.display_name

        display_image = True
        quantity = self.env.context.get('quantity', add_qty)
        context = dict(self.env.context, quantity=quantity, pricelist=pricelist.id if pricelist else False)
        product_template = self.with_context(context)

        combination = combination or product_template.env['product.template.attribute.value']

        if not product_id and not combination and not only_template:
            combination = product_template._get_first_possible_combination(parent_combination)

        if only_template:
            product = product_template.env['product.product']
        elif product_id and not combination:
            product = product_template.env['product.product'].browse(product_id)
        else:
            product = product_template._get_variant_for_combination(combination)

        if product:
            # We need to add the price_extra for the attributes that are not
            # in the variant, typically those of type no_variant, but it is
            # possible that a no_variant attribute is still in a variant if
            # the type of the attribute has been changed after creation.
            no_variant_attributes_price_extra = [
                ptav.price_extra for ptav in combination.filtered(
                    lambda ptav:
                        ptav.price_extra and
                        ptav not in product.product_template_attribute_value_ids
                )
            ]
            if no_variant_attributes_price_extra:
                product = product.with_context(
                    no_variant_attributes_price_extra=tuple(no_variant_attributes_price_extra)
                )
            list_price = product.price_compute('list_price')[product.id]
            price = product.price if pricelist else list_price
            display_image = bool(product.image_1920)
            display_name = product.display_name
        else:
            product_template = product_template.with_context(current_attributes_price_extra=[v.price_extra or 0.0 for v in combination])
            list_price = product_template.price_compute('list_price')[product_template.id]
            price = product_template.price if pricelist else list_price
            display_image = bool(product_template.image_1920)

            combination_name = combination._get_combination_name()
            if combination_name:
                display_name = "%s (%s)" % (display_name, combination_name)

        if pricelist and pricelist.currency_id != product_template.currency_id:
            list_price = product_template.currency_id._convert(
                list_price, pricelist.currency_id, product_template._get_current_company(pricelist=pricelist),
                fields.Date.today()
            )
        if self.env.context.get('politica','') == 'without_discount' or (pricelist and pricelist.discount_policy == 'without_discount'):
            price_without_discount = list_price
        else:
            price_without_discount = price
        has_discounted_price = (pricelist or product_template).currency_id.compare_amounts(price_without_discount, price) == 1

        return {
            'product_id': product.id,
            'product_template_id': product_template.id,
            'display_name': display_name,
            'display_image': display_image,
            'price': price,
            'list_price': list_price,
            'has_discounted_price': has_discounted_price,
        }