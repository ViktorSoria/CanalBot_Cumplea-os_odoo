# -*- coding: utf-8 -*-

from odoo import api, models, fields

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    def _get_aggregated_product_quantities(self, **kwargs):
        """Include weight in the dict of aggregated products moved

        returns: dictionary {same_key_as_super: {same_values_as_super, weight: weight}, ...}
        """
        aggregated_move_lines = super()._get_aggregated_product_quantities(**kwargs)
        for k, v in aggregated_move_lines.items():
            v['weight'] = v['product_uom_rec']._compute_quantity(v['qty_done'], v['product'].uom_id) * v['product'].weight
        return aggregated_move_lines
