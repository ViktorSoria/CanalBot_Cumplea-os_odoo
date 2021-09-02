

from odoo import fields, models, api
import logging

_logger = logging.getLogger("Pos available")


class ProductProduct(models.Model):
    _inherit = "product.product"

    def available_qty(self,location=False):
        if not location:
            location = self.env['stock.location'].search([('usage','=','internal')])
        else:
            location = self.env['stock.location'].browse(location)
        quants = self.env['stock.quant']
        for l in location:
            quants += self.env['stock.quant']._gather(self, l)
        return [(q.location_id.name, q.available_quantity) for q in quants]


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
        _logger.warning(vals)
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
        return vals


class PosConfig(models.Model):
    _inherit = "pos.config"

    show_qtys = fields.Boolean(
        "Show Product Qtys", help="Show Product Qtys in POS", default=True
    )
    default_location_src_id = fields.Many2one(
        "stock.location", related="picking_type_id.default_location_src_id"
    )
