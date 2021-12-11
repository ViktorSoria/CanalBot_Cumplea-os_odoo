productos = self.env['product.template'].search([('is_published', '!=', True)])
for p in productos:
    p.is_published = True
self.env.cr.commit()