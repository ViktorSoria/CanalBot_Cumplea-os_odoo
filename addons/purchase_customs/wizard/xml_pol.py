# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging
from lxml import etree
import base64
from odoo.exceptions import ValidationError

_log = logging.getLogger("__ EXP XML:: %s" % __name__)


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
                # treat like dict - we assume that if the first two tags
                # in a series are different, then they are all different.
                if len(element) == 1 or element[0].tag != element[1].tag:
                    aDict = XmlDictConfig(element)
                # treat like list - we assume that if the first two tags
                # in a series are the same, then the rest are the same.
                else:
                    # here, we put the list in dictionary; the key is the
                    # tag name the list elements all share in common, and
                    # the value is the list itself
                    aDict = {element[0].tag: XmlListConfig(element)}
                # if the tag has attributes, add those to the dict
                if element.items():
                    aDict.update(dict(element.items()))
                self.update({element.tag: aDict})
            # this assumes that if you've got an attribute in a tag,
            # you won't be having any text. This may or may not be a
            # good idea -- time will tell. It works for the way we are
            # currently doing XML configuration files...
            elif element.items():
                self.update({element.tag: dict(element.items())})
            # finally, if there are no child tags and no attributes, extract
            # the text
            else:
                self.update({element.tag: element.text})


class XmlToPol(models.TransientModel):
    _name = "xml.to.pol"
    _description = "Invoice XML to purchase order line importer"

    xml_file = fields.Binary(string="Archivo XML")
    xml_file_name = fields.Char(string="Nombre")

    def do_import(self):
        pre = "{http://www.sat.gob.mx/cfd/3}"
        xml_element = etree.XML(base64.b64decode(self.xml_file))
        # xml_doc = etree.tostring(xml_element, encoding='unicode')
        xmldict = XmlDictConfig(xml_element)
        conceptos = xmldict[pre+"Conceptos"][pre+"Concepto"]
        if len(conceptos) > 0:
            pols = []
            po = self._context.get("purchase_id")
            po_id = self.env['purchase.order'].browse(po)
            for co in conceptos:
                line_vals = {}
                # Line information
                product_id = self.env['product.template'].search([('default_code', '=like', co['NoIdentificacion'])])
                if not product_id:
                    continue
                product_qty = float(co['Cantidad'])
                product_uom_id = self.env['uom.uom'].search([('unspsc_code_id.code', '=like', co['ClaveUnidad'])])
                if not product_uom_id:
                    continue
                line_vals['product_id'] = product_id.id
                line_vals['product_qty'] = product_qty
                line_vals['product_uom'] = product_uom_id.id
                line_vals['price_unit'] = co['ValorUnitario']
                pols.append((0, 0, line_vals))
            po_id.order_line = pols
        else:
            raise ValidationError("No se encontraron lineas en la factura.")



# class XmlToPolLine(models.TransientModel):
#     _name = "xml.to.pol.line"
#     _description = "Temporal Invoice lines to check it before."
#
#     xml2pol_id = fields.Many2one('xml.to.pol', string="importer")
#     to_import = fields.Boolean(string="Para importar", default=False)
#
#     # Purchase order line fields.
#     product_id = fields.Many2one('product.template', string="Producto")
#     product_qty = fields.Float(string="Cantidad")
