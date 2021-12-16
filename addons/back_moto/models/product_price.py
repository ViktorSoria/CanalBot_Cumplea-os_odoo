

from odoo import fields, models, api
from odoo.exceptions import UserError
import xlrd
import tempfile
import csv
from io import StringIO
import base64
import logging

_logger = logging.getLogger("Moto Control")


class ProductTemplate(models.Model):
    _inherit = "product.template"

    line_ids = fields.Many2many("product.price.transient",string="Precios",compute="compute_line_price")

    def compute_line_price(self):
        products = [(product,False,False) for product in self]
        data = self.env['product.pricelist'].search([('lista_precio','=',True)])._compute_price_rule_multi(products)
        tarifas = self.env['product.pricelist'].search_read(fields=['id', 'name'])
        tarifas = {d['id']:d['name'] for d in tarifas}
        for p in self:
            prices = [{'name':"Precio del Producto",'precio':p.list_price,"product_id": p.id}]
            data_p = data[p.id]
            for tarifa,precio in data_p.items():
                prices.append({
                    'name': tarifas[tarifa],
                    "precio": precio[0],
                    "item_id": precio[1],
                    "list_price_id": tarifa,
                    "product_id": p.id,
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

    def change_price(self):
        if self.item_id and self.item_id.product_tmpl_id.id == self.product_id.id:
            self.item_id.write({'compute_price':'fixed','fixed_price':self.precio})
        elif self.list_price_id:
            self.list_price_id.write({'item_ids':[(0,0,{'compute_price':'fixed','fixed_price':self.precio,'applied_on':'1_product','product_tmpl_id':self.product_id.id})]})
        else:
            self.product_id.write({'list_price':self.precio})

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
            raise UserError("Formato de archivo incorrecto")
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
                if self.id==1:
                    p.list_price = float(l[1])
                elif not item:
                    new_items.append([0,0,{'applied_on':'1_product','compute_price':'fixed','fixed_price':float(l[1]),
                                          'product_tmpl_id':p.id}])
                else:
                    item.write({'fixed_price':float(l[1])})
            except:
                raise UserError("Erro en la linea: %s"%str(l))
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