# coding: utf-8

from os.path import join, dirname, realpath
from odoo import api, SUPERUSER_ID
import csv


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})

    stock_location = env['stock.location']
    stock_internal = env['stock.location'].search([('usage','=','internal')])
    warehouses = env['stock.warehouse']
    routes = env['stock.location.route']
    rules = env['stock.rule']

    route_rec = routes.create({
        'name': "Traspasos a Sucursales",
        'product_selectable': True,
        'warehouse_selectable': True,
        'warehouse_ids': [(6, 0, warehouses.search([]).ids)]
    })

    for stock in stock_internal:
        location_rec = stock_location.sudo().create({
            'name': "Transito a " + stock.display_name,
            'location_id': env.ref('stock.stock_location_locations_virtual').id,
            'usage': 'transit'
        })
        stock.write({'virtual_location': location_rec.id})
        warehouse_location = warehouses.search([('view_location_id', '=', stock.location_id.id)])
        type_id = warehouse_location.in_type_id.id if warehouse_location else False
        rule_rec = rules.sudo().create({
            'name': "Regla " + stock.display_name,
            'action': 'push',
            'picking_type_id': type_id,
            'location_src_id': location_rec.id,
            'location_id': stock.id,
            'auto': 'manual',
            'route_id': route_rec.id
        })



