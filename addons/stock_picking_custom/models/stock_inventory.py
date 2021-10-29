# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
from datetime import datetime
import logging
import io
import xlrd
import base64
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter

_log = logging.getLogger("stock_inventory (%s) -------> " % __name__)


class StockInventoryCustomWizard(models.TransientModel):
    _name = "wizard.warning"

    msg = fields.Text()

    def accept(self):
        pass


class StockInventoryCustom(models.Model):
    _inherit = "stock.inventory"

    category_products_PDV = fields.Many2many('pos.category', relation='model_act', string="Categoria PDV")
    is_file = fields.Boolean(string="Importación por archivo")
    import_file = fields.Binary(string="Archivo Excel")
    msg = fields.Text()
    stored_data = fields.Text()

    @api.onchange('category_products_PDV')
    def _calc_products(self):
        #Agrega productos
        products = self.env['product.product'].search([('pos_categ_id', 'in', self.category_products_PDV.ids), ('id', 'not in', self.product_ids.ids)])
        self.write({'product_ids': [(6, 0, products.ids)]})

    @api.onchange('import_file')
    def readfile(self):
        if self.import_file:
            inputx = io.BytesIO()
            inputx.write(base64.decodebytes(self.import_file))
            book = xlrd.open_workbook(file_contents=inputx.getvalue())
            sheet = book.sheets()[0]

            last_col = sheet.ncols-1
            code_list = {}
            msg=""
            for i in range(1,sheet.nrows):
                code_list[str(sheet.cell_value(i, 0))] = sheet.cell_value(i, last_col)

            products = self.env['product.product'].search([('default_code', 'in', list(code_list.keys()))])
            self.write({'product_ids': [(6, 0, products.ids)]})

            sobrantes = list(set(list(code_list.keys())) - set(products.mapped('default_code')))
            if sobrantes:
                for sobrante in sobrantes:
                    msg += str(sobrante) + ": El codigo no pudo ser localizado\n"
                    del code_list[str(sobrante)]
            data = ' '.join([str(key)+"@"+str(value) for key, value in code_list.items()])
            self._origin.write({'stored_data': data})
            if msg:
                return {
                    'warning': {
                        'title': 'Error al cargar los siguientes productos:',
                        'message': msg}
                }

    def action_start(self):
        res = super(StockInventoryCustom, self).action_start()
        if self.is_file and self.stored_data:
            products_list = list(self.stored_data.split(" "))
            self.msg = ""
            for product in products_list:
                product_l = product.split("@")
                flag_found = False
                for line in self.line_ids:
                    if line.product_id.default_code == product_l[0]:
                        _log.info("Encontre el producto")
                        flag_found = True
                        if product_l[1]:
                            try:
                                line.product_qty = float(product_l[1])
                            except ValueError:
                                self.msg += str(product_l) + ": La cantidad introducida no es un numero\n"
                        continue
                if not flag_found:
                        self.msg += str(product_l) + ": El producto no existe en la ubicación\n"
        if self.msg != "":
            self.msg = "Los siguientes productos no pudieron asignarse:\n\n" + self.msg
            return {
                'name': _("Los siguiente productos no pudieron asignarse"),  # Name You want to display on wizard
                'view_mode': 'form',
                'view_id': self.env.ref('stock_picking_custom.wizard_warning_data').id,
                'view_type': 'form',
                'res_model': 'wizard.warning',  # With . Example sale.order
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': {'default_msg': self.msg}
            }
        return res


class StockMoveCustom(models.Model):
    _inherit = "stock.move"

    def calc_productqty(self):

        squant = self.env['stock.quant'].search([('location_id', '=', self.location_id.id),
                                                 ('product_id', '=', self.product_id.id)])
        # _log.info("Está calculando cual es el stock actual:::  %s qty: %s " % (squant, squant.quantity))

        act_qty = squant.quantity
        # act_qty = squant.available_quantity

        return act_qty


class StockQuantWizard(models.TransientModel):
    _name = "wizard.download.data"

    location_id = fields.Many2one('stock.location', string='Ubicación')
    stock_quants_ids = fields.Many2many('stock.quant', string='Existencias')
    excel_file = fields.Binary('excel file')
    file_name = fields.Char('Nombre del Archivo', size=128)

    @api.onchange('location_id')
    def compute_quants(self):
        if self.location_id:
            self.stock_quants_ids = self.location_id.quant_ids
        else:
            self.stock_quants_ids = None

    def download_data(self):
        _log.info('Button')

        self.file_name = 'Existencias %s %s.xlsx' % (self.location_id.name, str(datetime.now()))
        fp = io.BytesIO()
        workbook = xlsxwriter.Workbook(fp, {'in_memory': True})
        encabezados = workbook.add_format(
            {'bold': 'True', 'font_size': 12, 'bg_color': '#B7F9B0', 'center_across': True})
        sheet = workbook.add_worksheet('Libro 1')
        sheet.set_column(0, 0, 10)
        sheet.set_column(1, 1, 15)
        sheet.set_column(2, 2, 8)
        sheet.set_column(3, 5, 20)
        sheet.set_column(6, 8, 15)
        sheet.write(0, 0, 'Codigo', encabezados)
        sheet.write(0, 1, 'Descripción', encabezados)
        sheet.write(0, 2, 'Sucursal', encabezados)
        sheet.write(0, 3, 'Cantidad Teorica', encabezados)
        sheet.write(0, 4, 'Cantidad Real', encabezados)
        r = 1
        for l in self.stock_quants_ids:
            sheet.write(r, 0, str(l.product_id.default_code) if l.product_id.default_code else '')
            sheet.write(r, 1, l.product_id.name)
            sheet.write(r, 2, self.location_id.display_name if self.location_id else '')
            sheet.write(r, 3, l.available_quantity)
            sheet.write(r, 4, '')
            r += 1

        workbook.close()
        fp.seek(0)
        self.excel_file = base64.encodestring(fp.getvalue())
        fp.close()
        url = self.env['ir.config_parameter'].get_param('web.base.url')
        file_url = url + "/web/binary/download_document?model=wizard.download.data&id=%s&field=excel_file&filename=%s" % (
        self.id, self.file_name)
        return {
            'type': 'ir.actions.act_url',
            'url': file_url,
        }

