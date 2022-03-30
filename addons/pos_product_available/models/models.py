from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
import logging
from odoo.addons.web.controllers.main import DataSet
from datetime import timedelta, datetime
from odoo.http import request
import json

_logger = logging.getLogger("Pos available")


class loadData(models.Model):
    _name = "load.data.pos"

    name = fields.Char("Model")
    text = fields.Char("Model")
    location_id = fields.Many2one("stock.location")

    def cron_delete_data(self):
        self.env.cr.execute("Delete from load_data_pos;")
        self.env.cr.commit()

    def cron_data_pos(self):
        self.env.cr.execute("Delete from load_data_pos;")
        self.env.cr.commit()
        model = 'product.product'
        fields = ['display_name', 'lst_price', 'standard_price', 'categ_id', 'pos_categ_id', 'taxes_id', 'barcode',
                  'default_code', 'to_weight', 'uom_id', 'description_sale', 'description', 'product_tmpl_id',
                  'tracking', 'write_date', 'available_in_pos', 'attribute_line_ids', "qty_available", "type",
                  'display_name']
        order = 'sequence, default_code, name'
        pos = self.env['pos.config'].search([])
        prod = pos.mapped('producto_cargo').ids
        load = self.env['load.data.pos']
        locations = {}
        for c in pos:
            if locations.get(c.default_location_src_id.id):
                pass
            domain = ['|', '&', ['sale_ok', '=', True], ['available_in_pos', '=', True], ('id', 'in', prod)]
            context = {'location': c.default_location_src_id.id}
            res = self.env[model].with_context(context).search_read(domain=domain, fields=fields, order=order)
            text = json.dumps(res, default=str)
            load.create({'location_id': c.default_location_src_id.id, 'name': model, 'text': text})
            locations[c.default_location_src_id.id] = True
        domain = [('pricelist_id', 'in', pos[0].available_pricelist_ids.ids)]
        res = self.env['product.pricelist.item'].search_read(domain=domain)
        text = json.dumps(res, default=str)
        load.create({'name': 'product.pricelist.item', 'text': text})


class controll(DataSet):

    def _call_kw(self, model, method, args, kwargs):
        res = None
        if model == 'product.pricelist.item' and kwargs.get('context',{}).get('global'):
            res = request.env['load.data.pos'].search([('name','=','product.pricelist.item')],limit=1,order="create_date desc")
            res = json.loads(res.text) if res else False
        elif model == 'product.product' and kwargs.get('context',{}).get('global'):
            res = request.env['load.data.pos'].search([('name','=','product.product'),('location_id','=',kwargs.get('context').get('location'))],limit=1,order="create_date desc")
            res = json.loads(res.text) if res else False
        if not res:
            res = super()._call_kw(model, method, args, kwargs)
        return res


class SyncDataPosProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def create(self, vals):
        producto = super(SyncDataPosProduct, self).create(vals)
        rec = self.env["pos.metadatos"].sudo()
        rec.nuevosDatos(self, create=True)
        return producto

    def write(self, vals):
        producto = super(SyncDataPosProduct, self).write(vals)
        rec = self.env["pos.metadatos"].sudo()
        campos = self.env['pos.metadatos'].search([('modelo','=','1')]).mapped("campos.name")
        campos = [c for c in campos if c in vals]
        if campos:
            if "list_price" in vals:
                campos.append('lst_price')
            if "name" in vals:
                campos.append('display_name')
            rec.nuevosDatos(self, campos)
        return producto


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def write(self, vals):
        producto = super(ProductTemplate, self).write(vals)
        rec = self.env["pos.metadatos"].sudo()
        campos = self.env['pos.metadatos'].search([('modelo','=','1')]).mapped("campos.name")
        campos = [c for c in campos if c in vals]
        if campos:
            if "list_price" in vals:
                campos.append('lst_price')
            if "name" in vals:
                campos.append('display_name')
            rec.nuevosDatos(self.product_variant_id, campos)
        return producto


class SyncDataPosPricelist(models.Model):
    _inherit = "product.pricelist.item"

    @api.model
    def create(self, vals):
        lstPrecios = super(SyncDataPosPricelist, self).create(vals)
        rec = self.env["pos.metadatos"].sudo()
        rec.nuevosDatos(lstPrecios, create=True)
        return lstPrecios

    def write(self, vals):
        item = super(SyncDataPosPricelist, self).write(vals)
        rec = self.env["pos.metadatos"].sudo()
        campos = self.env['pos.metadatos'].search([('modelo', '=', '2')]).mapped("campos.name")
        campos = [c for c in campos if c in vals]
        if campos:
            rec.nuevosDatos(self, campos+['pricelist_id'])
        return item


class SyncDataPosPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def create(self, vals):
        cliente = super(SyncDataPosPartner, self).create(vals)
        rec = self.env["pos.metadatos"].sudo()
        rec.nuevosDatos(cliente, create=True)
        return cliente

    def write(self, vals):
        partner = super(SyncDataPosPartner, self).write(vals)
        rec = self.env["pos.metadatos"].sudo()
        campos = self.env['pos.metadatos'].search([('modelo', '=', '3')]).mapped("campos.name")
        campos = [c for c in campos if c in vals]
        if campos:
            rec.nuevosDatos(self, campos)
        return partner


class TemporalDataPos(models.TransientModel):
    _name = "data.pos.metadatos"

    @api.model
    def update_data_pos(self,segundos):
        t = fields.Datetime.now() - timedelta(seconds=segundos+5)
        val = self.search_read([("create_date", ">", t)], fields=["modelo", 'rec_id', 'datos'],
                               order='create_date asc')
        return val

    modelo = fields.Char(string="Modelo")
    rec_id = fields.Integer(string="Id")
    datos = fields.Char(string="Campos")


class ConfigSyncPos(models.Model):
    _name = "pos.metadatos"

    def nuevosDatos(self, obj, campos=(), create=False):
        vals = {}
        if not create:
            for s in campos:
                x = obj.__getattribute__(s)
                if isinstance(x, models.Model):
                    vals[s] = [x.id, x.name]
                else:
                    vals[s] = x

        datos = {
            'modelo': obj._name,
            'rec_id': obj.id,
            'datos': json.dumps(vals)
        }

        self.env["data.pos.metadatos"].sudo().create(datos)

    @api.onchange('modelo')
    def filtrarCampos(self):
        """Obtiene el dominio para el campo 'campos' y se filtra todos los campos con 'store=True' del respectivo modelo"""
        self.campos = None
        dom = []

        if self.modelo == "1":
            mod = 'product.product'
        elif self.modelo == "2":
            mod = 'product.pricelist.item'
        elif self.modelo == "3":
            mod = 'res.partner'

        dom.extend([('model_id', '=', mod)])
        return {'domain': {'campos': dom}}

    modelo = fields.Selection([('1', 'Productos'), ('2', 'Lista de precios'), ('3', 'Clientes')], required=True,
                              default='1')
    campos = fields.Many2many("ir.model.fields", string="Campos")


class ProductProduct(models.Model):
    _inherit = "product.product"

    def available_qty(self, location=False):
        if not location:
            location = self.env['stock.location'].search([('usage', '=', 'internal')])
        else:
            location = self.env['stock.location'].browse(location)
        quants = self.env['stock.quant']
        for l in location:
            quants += self.env['stock.quant']._gather(self, l)
        return [(q.location_id.display_name, q.available_quantity) for q in quants]


class PosPaymentMethod(models.Model):
    _inherit = "pos.payment.method"

    l10n_mx_edi_payment_method_id = fields.Many2one('l10n_mx_edi.payment.method', string="Forma de pago")


class PosOrder(models.Model):
    _inherit = "pos.order"

    @api.model
    def _order_fields(self, ui_order):
        vals = super()._order_fields(ui_order)
        vals['l10n_mx_edi_usage'] = ui_order.get('to_invoice')
        vals['to_invoice'] = True if ui_order.get('to_invoice') else False
        return vals

    payment_method_id = fields.Many2one('pos.payment.method', "Metodo de Pago", compute="get_payment_method",
                                        store=True)
    l10n_mx_edi_usage = fields.Selection(
        selection=[
            ('G01', 'Adquisición de mercancías'),
            ('G02', 'Devoluciones, descuentos o bonificaciones'),
            ('G03', 'Gastos en general'),
            ('I01', 'Construcciones'),
            ('I02', 'Mobilario y equipo de oficina por inversiones'),
            ('I03', 'Equipo de transporte'),
            ('I04', 'Equipo de cómputo y accesorios'),
            ('I05', 'Dados, troqueles, moldes, matrices y herramental'),
            ('I06', 'Comunicaciones telefónicas'),
            ('I07', 'Comunicaciones satelitales'),
            ('I08', 'Otra maquinaria y equipo'),
            ('D01', 'Honorarios médicos, dentales y gastos hospitalarios'),
            ('D02', 'Gastos médicos por incapacidad o discapacidad'),
            ('D03', 'Gastos funerales'),
            ('D04', 'Donativos'),
            ('D05', 'Intereses reales efectivamente pagados por créditos hipotecarios (casa habitación)'),
            ('D06', 'Aportaciones voluntarias al SAR'),
            ('D07', 'Primas por seguros de gastos médicos'),
            ('D08', 'Gastos de transportación escolar obligatoria.'),
            ('D09', 'Depósitos en cuentas para el ahorro, primas que tengan como base planes de pensiones.'),
            ('D10', 'Pagos por servicios educativos (colegiaturas)'),
            ('P01', 'Pör definir'),
        ],
        string="Uso",
        default='P01')

    @api.depends('payment_ids')
    def get_payment_method(self):
        for rec in self:
            formas = {}
            for pay in rec.payment_ids:
                formas[pay.payment_method_id.id] = formas.get(pay.payment_method_id.id, 0) + pay.amount
            met = sorted(formas.items(), key=lambda x: x[1])
            rec.payment_method_id = met[0] if met else False

    def _prepare_invoice_vals(self):
        vals = super(PosOrder, self)._prepare_invoice_vals()
        vals['l10n_mx_edi_payment_method_id'] = self.payment_method_id.l10n_mx_edi_payment_method_id.id
        vals['l10n_mx_edi_usage'] = self.l10n_mx_edi_usage
        vals['pricelist_id'] = self.pricelist_id
        return vals

    def action_pos_order_invoice(self):
        moves = self.env['account.move']

        for order in self:
            # Force company for all SUPERUSER_ID action
            if order.account_move:
                moves += order.account_move
                continue

            if not order.partner_id:
                raise UserError(_('Please provide a partner for the sale.'))

            move_vals = order._prepare_invoice_vals()
            new_move = order._create_invoice(move_vals)
            order.write({'account_move': new_move.id, 'state': 'invoiced'})
            new_move.sudo().with_company(order.company_id)._post()
            moves += new_move
        moves.action_process_edi_web_services()
        if not moves:
            return {}

        return {
            'name': _('Customer Invoice'),
            'view_mode': 'form',
            'view_id': self.env.ref('account.view_move_form').id,
            'res_model': 'account.move',
            'context': "{'move_type':'out_invoice'}",
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': moves and moves.ids[0] or False,
        }


class PosConfig(models.Model):
    _inherit = "pos.config"

    show_qtys = fields.Boolean(
        "Show Product Qtys", help="Show Product Qtys in POS", default=True
    )
    default_location_src_id = fields.Many2one(
        "stock.location", related="picking_type_id.default_location_src_id", store=True
    )
