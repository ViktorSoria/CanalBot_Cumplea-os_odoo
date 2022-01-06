productos = self.env['product.template'].search([('is_published', '!=', True)])
for p in productos:
    p.is_published = True
self.env.cr.commit()

for p in location:
    v = product.with_context(location=p.id).virtual_available
    if v>0:
        print(p.display_name)


productos = self.env['product.template'].search([])
prod = productos.filtered(lambda p: p.image_1920)
pr = {prod.default_code:prod.image_1920}

env = Enviroment.conetion
productos = env['product.template'].search([])
for p in productos:
    imagen = pr[p.prod.default_code]
    p.image_1920 = imagen
