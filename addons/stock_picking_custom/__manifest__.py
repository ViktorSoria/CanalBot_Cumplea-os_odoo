{
    "name": "Customización de inventario",
    "summary": "Módulo con customizaciones",
    "author": "Tekniu: Isaac, Jehosafat",
    "depends": [
        "base", "stock", "crm", "point_of_sale", "sale_stock", "stock", "sale", "sale_management", "hr"
    ],
    "installable": True,
    "data": [
        "security/ir.model.access.csv",
        "report/picking_report.xml",
        "report/stock_quant_pack_report.xml",
        "report/stocks_pdf_report.xml",
        "views/stock_picking.xml",
        "views/stock_inventory_wizard.xml",
        "views/stock_inventory_views.xml",
        # "views/stock_templates.xml"
    ],
    'qweb': [
        # 'static/src/xml/stock_template_button.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'auto_install': True,
}