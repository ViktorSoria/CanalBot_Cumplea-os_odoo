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

    def validate_qty(self, codigo, cantidad,sucursal,productos,locaciones):
        #valida producto
        p = productos[codigo] if productos.get(codigo) else None
        if not p:
            return {'msg': codigo + ': El codigo no ha sido encontrado'}
        dic={
            'product_id': p[0],
            'product_uom_id': p[1]
        }
        #valida cantidad
        try:
            dic['product_qty'] = float(cantidad)
        except ValueError:
            return {'msg' : codigo + ": La cantidad introducida no es un numero (" + str(cantidad) + ")"}
        #valida sucursal
        l = locaciones[sucursal] if sucursal and locaciones.get(sucursal) else None
        if not l:
            if self.location_ids and len(self.location_ids.ids) == 1:
                dic['location_id'] = self.location_ids[0].id
            else:
                return {'msg': codigo + ": Sucursal no esta bien definida en el excel o en el Ajuste de Inventario"}
        else:
            dic['location_id'] = l
        return dic

    def create_data(self):
        inputx = io.BytesIO()
        inputx.write(base64.decodebytes(self.import_file))
        book = xlrd.open_workbook(file_contents=inputx.getvalue())
        sheet = book.sheets()[0]
        suc_col = None
        last_col = sheet.ncols - 1
        for i in range(sheet.ncols):
            if sheet.cell_value(0, i) == 'Cantidad Real':
                last_col = i
            if sheet.cell_value(0, i) == 'Sucursal':
                suc_col = i
        code_list = []
        codes = []
        for i in range(1, sheet.nrows):
            codigo_producto = str(sheet.cell_value(i, 0))
            cantidad = sheet.cell_value(i, last_col)
            sucursal = sheet.cell_value(i, suc_col) if suc_col else None
            code_list.append([codigo_producto,cantidad,sucursal])
            codes.append(codigo_producto)
        return [code_list,codes]

    def initialize_action(self):
        code_list,codigos = self.create_data()
        _log.info(code_list)
        msg = ""
        products = self.env['product.product'].search([('default_code', 'in', codigos)])
        locations = self.env['stock.location'].search([('usage', '=', 'internal')])
        productos_dic = {p.default_code: [p.id,p.uom_id.id] for p in products}
        loca_dic = {l.display_name: l.id for l in locations}
        lines = []
        sucs = []
        for code, qty, suc in code_list:
            data = self.validate_qty(codigo=code,cantidad=qty,sucursal=suc,productos=productos_dic,locaciones=loca_dic)
            _log.info(data)
            if data.get('msg'):
                msg += '\n'+data.get('msg')
            else:
                lines.append((0,0,data))
                if data.get('location_id') and (4, data['location_id']) not in sucs and data['location_id'] not in self.location_ids.ids:
                    sucs.append((4, data['location_id']))
        return {'msg':msg,'locations':sucs,'lines':lines}

    def action_open_inventory_lines_from_button(self):
        self.ensure_one()
        action = {
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'name': _('Inventory Lines'),
            'res_model': 'stock.inventory.line',
        }
        context = {
            'default_is_editable': False,
            'default_inventory_id': self.id,
            'default_company_id': self.company_id.id,
        }
        domain = [
            ('inventory_id', '=', self.id),
            ('location_id.usage', 'in', ['internal', 'transit'])
        ]
        if len(self.location_ids) == 1:
            if not self.location_ids[0].child_ids:
                context['readonly_location_id'] = True

        action['view_id'] = self.env.ref('stock_picking_custom.stock_inventory_line_tree_no_create').id
        action['context'] = context
        action['domain'] = domain
        return action

    def action_start(self):
        msg=""
        flag_super =True
        try:
            if self.is_file and self.import_file:
                res = self.initialize_action()
                msg = res.get('msg')
                _log.info(res)
                self.sudo().write({
                    'line_ids': res.get('lines'),
                    'location_ids': res.get('locations')
                })
            elif self.is_file and not self.import_file:
                msg = "Defina un archivo a cargar en \"Archivo Excel\""
                flag_super = False
            if self.is_file and self.import_file and res and not res.get('lines'):
                msg = "Ningun Producto pudo cargarse del excel, favor de revisarlo:\n" + msg
                flag_super = False
        except Exception as e:
            msg = str(e)

        result = super(StockInventoryCustom, self).action_start() if flag_super else None
        if msg != "":
            return {
                'name': _("Los siguiente productos no pudieron asignarse"),  # Name You want to display on wizard
                'view_mode': 'form',
                'view_id': self.env.ref('stock_picking_custom.wizard_warning_data').id,
                'view_type': 'form',
                'res_model': 'wizard.warning',  # With . Example sale.order
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': {'default_msg': msg}
            }
        else:
            return result


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
        if self.location_id:
            self.file_name = 'Existencias %s %s.xlsx' % (self.location_id.display_name, str(datetime.now()))
        else:
            self.file_name = 'Existencias %s.xlsx' % (str(datetime.now()))
        fp = io.BytesIO()
        workbook = xlsxwriter.Workbook(fp, {'in_memory': True})
        encabezados = workbook.add_format(
            {'bold': 'True', 'font_size': 12, 'bg_color': '#B7F9B0', 'center_across': True})
        sheet = workbook.add_worksheet('Libro 1')
        sheet.set_column(0, 0, 15)
        sheet.set_column(1, 1, 45)
        sheet.set_column(2, 2, 15)
        sheet.set_column(3, 5, 12)
        sheet.set_column(6, 8, 12)
        sheet.write(0, 0, 'Codigo', encabezados)
        sheet.write(0, 1, 'Descripción', encabezados)
        sheet.write(0, 2, 'Sucursal', encabezados)
        sheet.write(0, 3, 'Cantidad Teorica', encabezados)
        sheet.write(0, 4, 'Precio Unitario', encabezados)
        sheet.write(0, 5, 'Precio Total', encabezados)
        sheet.write(0, 6, 'Cantidad Real', encabezados)
        r = 1
        for l in self.stock_quants_ids:
            sheet.write(r, 0, str(l.product_id.default_code) if l.product_id.default_code else '')
            sheet.write(r, 1, l.product_id.name)
            sheet.write(r, 2, l.location_id.display_name if l.location_id else '')
            sheet.write(r, 3, l.available_quantity)
            sheet.write(r, 4, str(float(l.value/l.available_quantity)) if l.available_quantity != 0 else '0.0')
            sheet.write(r, 5, l.value)
            sheet.write(r, 6, '')
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

    def call_wizard_excel(self):
        if self._context.get('active_ids'):
            wizard = self.env["wizard.download.data"].create({
                'stock_quants_ids': [(6, 0, self._context.get('active_ids'))]
            })
            return wizard.download_data()

    class StockInventoryLineCustom(models.Model):
        _inherit = "stock.inventory.line"

        money_diff = fields.Float("Diferencia(MX)", compute='calculate_money_diff')
        cost_related = fields.Float("Costo Unitario",  related='product_id.standard_price')

        def calculate_money_diff(self):
            for rec in self:
                rec.money_diff = rec.difference_qty * rec.product_id.standard_price


