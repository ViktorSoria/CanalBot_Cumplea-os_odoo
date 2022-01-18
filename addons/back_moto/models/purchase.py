

from odoo import fields, models, api
from odoo.exceptions import UserError
import xlrd
import tempfile
import csv
from lxml import etree
from io import StringIO
import base64
import logging

_logger = logging.getLogger("Moto Control")


class XmlListConfig(list):
    def __init__(self, aList):
        for element in aList:
            if element:
                # treat like dict
                if len(element) == 1 or element[0].tag != element[1].tag:
                    self.append(XmlDictConfig(element))
                # treat like list
                elif element[0].tag == element[1].tag:
                    self.append(XmlListConfig(element))
            elif element.text:
                text = element.text.strip()
                if text:
                    self.append(text)


class XmlDictConfig(dict):
    def __init__(self, parent_element):
        if parent_element.items():
            self.update(dict(parent_element.items()))
        for element in parent_element:
            if element:
                if len(element) == 1 or element[0].tag != element[1].tag:
                    aDict = XmlDictConfig(element)
                else:
                    aDict = {element[0].tag: XmlListConfig(element)}
                if element.items():
                    aDict.update(dict(element.items()))
                self.update({element.tag: aDict})
            elif element.items():
                self.update({element.tag: dict(element.items())})
            else:
                self.update({element.tag: element.text})


class PurchaseLoad(models.TransientModel):
    _name = "purchase.order.lines.load"

    purchase_id = fields.Many2one("purchase.order",'Order',required=True)
    file_type = fields.Selection([
        ('xls', 'Archivo XLS'),
        ('csv', 'Archivo CSV'),
        ('xml', 'Archivo XML (factura)')
    ], string="Tipo", default="xls", required=True)
    file = fields.Binary("Seleccionar Archivo", required=True)
    product = fields.Selection([('default_code','Referencia Interna'),('barcode','Codigo de Barras'),
                                ('name','Nombre')], string="Importar producto por", required=True,default="default_code")
    detalles = fields.Selection([("product",'Producto'),("file",'Archivo')],string="Cargar detalles de",default="product",required=True)

    @api.model
    def _get_product_purchase_description(self, product_lang):
        name = product_lang.display_name
        if product_lang.description_purchase:
            name += '\n' + product_lang.description_purchase
        return name

    def create_data(self):
        data = []
        product = []
        if self.file_type == 'xls':
            file_path = tempfile.gettempdir() + '/file.xls'
            f = open(file_path, 'wb')
            f.write(base64.b64decode(self.file))
            f.close()
            workbook = xlrd.open_workbook(file_path)
            sh = workbook.sheet_by_index(0)
            for i in range(1,sh.nrows):
                l = sh.row(i)
                p = self.env['product.product'].search([(self.product,'=',l[0].value)],limit=1)
                if not p:
                    product.append(str([new.value for new in l]))
                    continue
                d = {
                    'product_id': p.id,
                    "product_qty": float(l[1].value),
                    "name": self._get_product_purchase_description(p)
                }
                if self.detalles == 'file':
                    d['price_unit'] = float(l[2].value)
                else:
                    d['price_unit'] = p.standard_price
                data.append([0,0,d])
        elif self.file_type == 'csv':
            csv_file = base64.b64decode(self.file).decode()
            file_input = StringIO(csv_file)
            file_input.seek(0)
            reader = csv.reader(file_input, delimiter=',')
            lines = []
            lines.extend(reader)
            for l in lines[1:]:
                p = self.env['product.product'].search([(self.product, '=', l[0])],limit=1)
                if not p:
                    product.append(str(l))
                    continue
                d = {
                    'product_id': p.id,
                    "product_qty": float(l[1]),
                    "name": self._get_product_purchase_description(p)
                }
                if self.detalles == 'file':
                    d['price_unit'] = float(l[2])
                else:
                    d['price_unit'] = p.standard_price
                data.append([0, 0, d])
        elif self.file_type == 'xml' and self.file:
            pre = "{http://www.sat.gob.mx/cfd/3}"
            xml_element = etree.XML(base64.b64decode(self.file))
            # xml_doc = etree.tostring(xml_element, encoding='unicode')
            xmldict = XmlDictConfig(xml_element)
            conceptos = xmldict[pre + "Conceptos"][pre + "Concepto"]
            if len(conceptos) <= 0:
                raise UserError("XML sin lineas de producto o mal formado.")
            for co in conceptos:
                # _logger.info("LINEA ::: %s" % co)
                line_vals = {}
                # Line information
                # Select by default_code, name or barcode
                product_id = self.env['product.product'].search([(self.product, '=', co['NoIdentificacion'])], limit=1)
                if not product_id:
                    product.append(str(co))
                    continue
                product_qty = float(co['Cantidad'])
                # product_uom_id = self.env['uom.uom'].search([('unspsc_code_id.code', '=like', co['ClaveUnidad'])])
                # if not product_uom_id:
                #     continue
                line_vals['product_id'] = product_id.id
                line_vals['product_qty'] = product_qty
                # line_vals['product_uom'] = product_uom_id.id
                line_vals['price_unit'] = co['ValorUnitario'] if self.detalles == 'file' else product_id.standard_price
                data.append((0, 0, line_vals))

        return [data, product]

    def generate_lines(self):
        try:
            data,productos = self.create_data()
        except Exception as e:
            raise UserError('Error al cargar el archivo\n Asegurese de que el formato coincide con el archivo \n\n%s'%str(e))
        self.purchase_id.update({'order_line':[(5,0,0)]+data})
        if productos:
            mensaje = {
                'message': 'Algunos renglones no pudieron procesarse debido a que el producto no se encuentra en el sistema\n' + '\n'.join(
                    productos)}
            return {
                'name': 'Error Crear Pagos',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'message.wizard',
                'target': 'new',
                'context': mensaje
            }


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def load_lines(self):
        return {
            'name': "Cargar Lineas",
            'type': "ir.actions.act_window",
            'res_model': "purchase.order.lines.load",
            'view_mode': "form",
            'view_type': "form",
            'target': "new",
            "context": {"default_purchase_id":self.id}
        }

    def button_confirm(self):
        res = super(PurchaseOrder,self).button_confirm()
        for l in self.order_line:
            l.product_id.standard_price = l.price_unit
        return res


class wiardMessage(models.TransientModel):
    _name = 'message.wizard'

    def get_default(self):
        return self.env.context.get("message",False)

    name = fields.Text(string="Message",readonly=True,default=get_default)