# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
import datetime
import calendar
import logging

_log = logging.getLogger("stock_quant_package (%s) -------> " % __name__)


class StockQuantPackageCustom(models.Model):
    _inherit = "stock.quant.package"

    def get_empacador_name(self):
        # ESTA FUNCION VA Y BUSCA EL NOMBRE DEL EMPACADOR EN LA TRANSFERENCIA DONDE FUE CREADO EL PACK
        _log.info("Obteniendo el nombre del que empacará")