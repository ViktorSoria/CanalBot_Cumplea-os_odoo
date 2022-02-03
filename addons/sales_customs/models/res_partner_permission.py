from odoo import models, fields, api

class PermisoListaPrecios(models.Model):
    _inherit="sale.order"

    def priceListPermission(self):
        self.permiso_lista_precios=self.env.user.has_group('sales_customs.group_edition_price_list')

    permiso_lista_precios=fields.Boolean(string="Permitir modificar lista de precios", compute="priceListPermission")


class PermisoFacturascreditos(models.Model):
    _inherit="account.move"

    def creditInvoicePermission(self):
        self.permiso_saldo_aFavor=self.env.user.has_group('sales_customs.group_edition_invoices_credits')

    permiso_saldo_aFavor=fields.Boolean(string="Aplicacion de saldos a favor en facturas", compute="creditInvoicePermission")