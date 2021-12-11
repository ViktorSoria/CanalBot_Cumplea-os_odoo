# -*- coding: utf-8 -*-

{
    'name': 'Website custom',
    'summary': 'Website custom',
    'sequence': '1',
    'category': 'Website',
    'description': """
This module adds new some features about website and ecommerce portal.""",
    'depends': ['portal', 'point_of_sale', 'purchase',  'website_sale'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/pos_orders.xml',
        'views/product_lines.xml',
        'views/config_views.xml',
        'templates/assets.xml',
        'templates/website_products.xml',
    ],
    'qweb': [

    ],
}
