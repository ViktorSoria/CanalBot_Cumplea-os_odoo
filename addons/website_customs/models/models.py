# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
import logging

_log = logging.getLogger("Website (%s) -------> " % __name__)


class Location(models.Model):
    _inherit = "stock.location"

    dis_website = fields.Boolean("Disponible en sitio web",default=True)
    name_almacen = fields.Char("Nombre Almacen")
    promocion = fields.Boolean("Promocion")
    remate = fields.Boolean("Remate")


class List(models.Model):
    _inherit = "product.pricelist"

    relational_list = fields.Many2one("product.pricelist",'Lista relacionada')
    por_promo = fields.Float('Porcentaje promocion')
    por_remate = fields.Float('Porcentaje remate')
    promocion = fields.Boolean("Promocion y remate")


class Product(models.Model):
    _inherit = "product.product"

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
        for l in listas.filtered(lambda l: l.relational_list.promocion):
            lista_rel = l.relational_list
            lista_rel.mapped('item_ids').unlink()
            for p in remate:
                item_rel = l.item_ids.filtered(lambda i: i.product_tmpl_id.id == p[0])
                data = {
                    'applied_on': '1_product',
                    'product_tmpl_id': p[0],
                    'compute_price': 'fixed',
                    'fixed_price': item_rel.fixed_price*(100-lista_rel.por_remate)/100,
                    'pricelist_id': lista_rel.id
                }
                self.env['product.pricelist.item'].create(data)
            for p in promocion:
                item_rel = l.item_ids.filtered(lambda i: i.product_tmpl_id.id == p[0])
                data ={
                    'applied_on': '1_product',
                    'product_tmpl_id': p[0],
                    'compute_price': 'fixed',
                    'fixed_price': item_rel.fixed_price *(100-lista_rel.por_promo)/ 100,
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
            price=price,
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