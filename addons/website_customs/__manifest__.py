{
    "name": "Customización de Sitio web",
    "summary": "",
    "author": "Tekniu",
    "depends": [
        "website", "point_of_sale",'website_sale','website_sale_stock','im_livechat'
    ],
    "installable": True,
    "data": [
        'security/groups.xml',
        'template/assets.xml',
        'template/web.xml',
        'views/pricelist_views.xml',
        'views/visitor_views.xml',
        'views/snippets.xml',
        'data/data.xml',
        'views/no_edit.xml',
    ],
    'qweb': ['static/src/xml/snippets',
             ],
}
