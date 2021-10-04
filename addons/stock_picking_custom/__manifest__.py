{
    "name": "Customización de inventario",
    "summary": "Módulo con customizaciones",
    "author": "Tekniu: Isaac, Jehosafat",
    "depends": [
        "base", "stock", "crm", "point_of_sale"
    ],
    "installable": True,
    "data": [
        "report/picking_report.xml",
        "views/stock_picking.xml",
        "views/stock_inventory_views.xml"
    ],
    'post_init_hook': 'post_init_hook',
    'auto_install': True,
}