#Crear regla
env = self.env
stock_location = env['stock.location']
stock_internal = env['stock.location'].search([('usage','=','internal'), ('virtual_location', '=', False)])
warehouses = env['stock.warehouse']
rules = env['stock.rule']

#id de la ruta "Traspaso a sucursales" en el browse
route_rec = env['stock.location.route'].browse(66)
route_rec.write({
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



