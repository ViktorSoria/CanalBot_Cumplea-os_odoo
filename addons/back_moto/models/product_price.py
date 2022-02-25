from odoo import fields, models, api
from odoo.exceptions import UserError
import xlrd
import tempfile
import csv
from itertools import chain
from io import StringIO
import base64
import logging

_logger = logging.getLogger("Moto Control")


class ProductTemplate(models.Model):
    _inherit = "product.template"

    line_ids = fields.Many2many("product.price.transient",string="Precios",compute="compute_line_price")
    utili_perc = fields.Float("Utilidad (%)")

    def compute_line_price(self):
        products = [(product,False,False) for product in self]
        data = self.env['product.pricelist'].search([('lista_precio','=',True)]).with_context(margen=True)._compute_price_rule_multi(products)
        tarifas = self.env['product.pricelist'].search_read(fields=['id', 'name'])
        tarifas = {d['id']:d['name'] for d in tarifas}
        for p in self:
            prices = [{'name':"Precio del Producto",'precio':p.list_price,"product_id": p.id,'utili_perc':p.utili_perc}]
            data_p = data[p.id]
            for tarifa,precio in data_p.items():
                prices.append({
                    'name': tarifas[tarifa],
                    "precio": precio[0],
                    "item_id": precio[1],
                    "list_price_id": tarifa,
                    "product_id": p.id,
                    "utili_perc":precio[2],
                })
            lines = self.env['product.price.transient'].create(prices)
            p.line_ids = [(6,0,lines.ids)]

    def export_data(self,fields_to_export):
        """
        se agregan las lineas al archivo web/controllers/main.py en el metodo base(self, data, token)
        datas = records.export_data(field_names)
        export_data = datas.get('datas', [])
        columns_headers = datas.get('columns_headers', columns_headers)
        """
        res = super().export_data(fields_to_export)
        if "line_ids/precio" in fields_to_export and "line_ids/display_name":
            res = res.get('datas')
            listas = self.env['product.pricelist'].search([('lista_precio','=',True)])
            precio_index = fields_to_export.index("line_ids/precio")
            nombre_index = fields_to_export.index("line_ids/display_name")
            fields_to_export.pop(precio_index)
            fields_to_export.pop(nombre_index)
            new_res = []
            disp = (len(listas)+1)
            for i in range(len(res)//disp):
                add = []
                for j in range(disp):
                    precio = res[i*disp+j].pop(precio_index)
                    add.append(precio)
                    nombre = res[i*disp+j].pop(nombre_index)
                    if i==0:
                        fields_to_export.append(nombre)
                    if j==disp-1:
                        new_res.append(res[i*disp]+add)
            res = {'datas':new_res,'columns_headers':fields_to_export}
        return res


class ProducPrice(models.TransientModel):
    _name = "product.price.transient"

    name = fields.Char("Descripción")
    precio = fields.Float("Precio")
    item_id = fields.Many2one("product.pricelist.item","Item")
    list_price_id = fields.Many2one("product.pricelist","Lista")
    product_id = fields.Many2one("product.template")
    utili_perc = fields.Float("Utilidad (%)")

    @api.onchange('utili_perc')
    def onchange_margin(self):
        if self.utili_perc != 0:
            costo = self.product_id.standard_price
            self.precio = costo*1.16*(1+self.utili_perc/100)

    def change_price(self):
        if self.item_id and self.item_id.product_tmpl_id.id == self.product_id.id:
            self.item_id.write({'compute_price':'fixed','fixed_price':self.precio,'utili_perc':self.utili_perc})
        elif self.list_price_id:
            self.list_price_id.write({'item_ids':[(0,0,{'compute_price':'fixed','fixed_price':self.precio,'applied_on':'1_product','product_tmpl_id':self.product_id.id,'utili_perc':self.utili_perc})]})
        else:
            self.product_id.write({'list_price':self.precio,'utili_perc':self.utili_perc})

    def edit_line(self):
        return {
            'name': "Editar Precio",
            'type': "ir.actions.act_window",
            'res_model': "product.price.transient",
            'res_id': self.id,
            'view_mode': "form",
            'view_type': "form",
            'target': "new",
        }


class Pricelist(models.Model):
    _inherit = "product.pricelist"

    file = fields.Binary("Nuevos Precios (csv)")
    file_name = fields.Char("Nombre archivo")
    lista_precio = fields.Boolean("Lista de precio",default=True)
    option_select = fields.Selection([('price','Precio'),('util','Utilidad')], string='Opción')

    def get_lines(self):
        lines = []
        try:
            if 'csv' in self.file_name:
                csv_file = base64.b64decode(self.file).decode()
                file_input = StringIO(csv_file)
                file_input.seek(0)
                reader = csv.reader(file_input, delimiter=',')
                lines.extend(reader)
            else:
                file_path = tempfile.gettempdir() + '/file.xls'
                f = open(file_path, 'wb')
                f.write(base64.b64decode(self.file))
                f.close()
                workbook = xlrd.open_workbook(file_path)
                sh = workbook.sheet_by_index(0)
                for i in range(1, sh.nrows):
                    lines.append(sh.row_values(i))
        except:
            raise UserError("Erro en formato de archivo")
        return lines


    def update_price(self):
        if not self.file:
            return
        lines = self.get_lines()
        if len(lines[0])>2:
            raise UserError("Formato de archivo incorrecto, Ponga en una columna la referencia del producto y en otra el precio/utilidad")
        productos = self.env['product.template'].search([])
        productos = {p.default_code: p for p in productos}
        items = {i.product_tmpl_id.default_code:i for i in self.item_ids if i.product_tmpl_id}
        new_items = []
        faltantes = []
        for l in lines[1:]:
            try:
                p = productos.get(l[0])
                item = items.get(l[0])
                if not p:
                    faltantes.append(str(l))
                    continue
                float_value = float(l[1])
                price = float_value if self.option_select == 'price' else p.standard_price * (1 + float_value/100) * 1.16
                _logger.info(price)
                if not item:
                    dic = {'applied_on':'1_product','compute_price':'fixed','fixed_price':price, 'product_tmpl_id':p.id}
                    if self.option_select == 'util':
                        dic['utili_perc'] = float_value
                    new_items.append([0,0,dic])
                else:
                    dic = {'fixed_price':price}
                    if self.option_select == 'util':
                        dic['utili_perc'] = float_value
                    item.write(dic)
                if self.id == 1:
                    dic = {'list_price':price}
                    if self.option_select == 'util':
                        dic['utili_perc'] = float_value
                    p.write(dic)
            except:
                raise UserError("Error en la linea: %s"%str(l))
        self.write({'item_ids':new_items,'file':False})
        if faltantes:
            mensaje = "Los siguientes productos no fueron encontrados\n%s"%('\n'.join(faltantes))
            return {
                'name': 'Error Crear Pagos',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'message.wizard',
                'target': 'new',
                'context': mensaje
            }


class Line(models.Model):
    _inherit="sale.order.line"

    # @api.depends(
    #     'product_id', 'customer_lead', 'product_uom_qty', 'product_uom', 'order_id.commitment_date',
    #     'move_ids', 'move_ids.forecast_expected_date', 'move_ids.forecast_availability')
    # def _compute_qty_at_date(self):
    #     obj = self
    #     ware = self.mapped('warehouse_id')[:1]
    #     if ware:
    #         location = ware.lot_stock_id.id
    #         obj = self.with_context(location=location)
    #     super(Line,obj)._compute_qty_at_date()


class PriceListItem(models.Model):
    _inherit="product.pricelist.item"

    utili_perc = fields.Float("Utilidad (%)")


class Pricelistrule(models.Model):
    _inherit = "product.pricelist"

    def _compute_price_rule(self, products_qty_partner, date=False, uom_id=False):
        """ Low-level method - Mono pricelist, multi products
        Returns: dict{product_id: (price, suitable_rule) for the given pricelist}

        Date in context can be a date, datetime, ...

            :param products_qty_partner: list of typles products, quantity, partner
            :param datetime date: validity date
            :param ID uom_id: intermediate unit of measure
        """
        self.ensure_one()
        if not date:
            date = self._context.get('date') or fields.Datetime.now()
        if not uom_id and self._context.get('uom'):
            uom_id = self._context['uom']
        if uom_id:
            # rebrowse with uom if given
            products = [item[0].with_context(uom=uom_id) for item in products_qty_partner]
            products_qty_partner = [(products[index], data_struct[1], data_struct[2]) for index, data_struct in enumerate(products_qty_partner)]
        else:
            products = [item[0] for item in products_qty_partner]

        if not products:
            return {}

        categ_ids = {}
        for p in products:
            categ = p.categ_id
            while categ:
                categ_ids[categ.id] = True
                categ = categ.parent_id
        categ_ids = list(categ_ids)

        is_product_template = products[0]._name == "product.template"
        if is_product_template:
            prod_tmpl_ids = [tmpl.id for tmpl in products]
            # all variants of all products
            prod_ids = [p.id for p in
                        list(chain.from_iterable([t.product_variant_ids for t in products]))]
        else:
            prod_ids = [product.id for product in products]
            prod_tmpl_ids = [product.product_tmpl_id.id for product in products]

        items = self._compute_price_rule_get_items(products_qty_partner, date, uom_id, prod_tmpl_ids, prod_ids, categ_ids)

        results = {}
        for product, qty, partner in products_qty_partner:
            results[product.id] = 0.0
            suitable_rule = False

            # Final unit price is computed according to `qty` in the `qty_uom_id` UoM.
            # An intermediary unit price may be computed according to a different UoM, in
            # which case the price_uom_id contains that UoM.
            # The final price will be converted to match `qty_uom_id`.
            qty_uom_id = self._context.get('uom') or product.uom_id.id
            qty_in_product_uom = qty
            if qty_uom_id != product.uom_id.id:
                try:
                    qty_in_product_uom = self.env['uom.uom'].browse([self._context['uom']])._compute_quantity(qty, product.uom_id)
                except UserError:
                    # Ignored - incompatible UoM in context, use default product UoM
                    pass

            # if Public user try to access standard price from website sale, need to call price_compute.
            # TDE SURPRISE: product can actually be a template
            price = product.price_compute('list_price')[product.id]

            price_uom = self.env['uom.uom'].browse([qty_uom_id])
            for rule in items:
                if rule.min_quantity and qty_in_product_uom < rule.min_quantity:
                    continue
                if is_product_template:
                    if rule.product_tmpl_id and product.id != rule.product_tmpl_id.id:
                        continue
                    if rule.product_id and not (product.product_variant_count == 1 and product.product_variant_id.id == rule.product_id.id):
                        # product rule acceptable on template if has only one variant
                        continue
                else:
                    if rule.product_tmpl_id and product.product_tmpl_id.id != rule.product_tmpl_id.id:
                        continue
                    if rule.product_id and product.id != rule.product_id.id:
                        continue

                if rule.categ_id:
                    cat = product.categ_id
                    while cat:
                        if cat.id == rule.categ_id.id:
                            break
                        cat = cat.parent_id
                    if not cat:
                        continue

                if rule.base == 'pricelist' and rule.base_pricelist_id:
                    price_tmp = rule.base_pricelist_id._compute_price_rule([(product, qty, partner)], date, uom_id)[product.id][0]  # TDE: 0 = price, 1 = rule
                    price = rule.base_pricelist_id.currency_id._convert(price_tmp, self.currency_id, self.env.company, date, round=False)
                else:
                    # if base option is public price take sale price else cost price of product
                    # price_compute returns the price in the context UoM, i.e. qty_uom_id
                    price = product.price_compute(rule.base)[product.id]

                if price is not False:
                    price = rule._compute_price(price, price_uom, product, quantity=qty, partner=partner)
                    suitable_rule = rule
                break
            # Final price conversion into pricelist currency
            if suitable_rule and suitable_rule.compute_price != 'fixed' and suitable_rule.base != 'pricelist':
                if suitable_rule.base == 'standard_price':
                    cur = product.cost_currency_id
                else:
                    cur = product.currency_id
                price = cur._convert(price, self.currency_id, self.env.company, date, round=False)

            if not suitable_rule:
                cur = product.currency_id
                price = cur._convert(price, self.currency_id, self.env.company, date, round=False)
            if self.env.context.get("margen"):
                results[product.id] = (price, suitable_rule and suitable_rule.id or False,suitable_rule and suitable_rule.utili_perc or 0)
            else:
                results[product.id] = (price, suitable_rule and suitable_rule.id or False)
        return results