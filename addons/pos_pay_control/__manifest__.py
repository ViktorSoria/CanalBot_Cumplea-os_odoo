
{
    "name": """POS: pay Control""",
    "summary": """Permisos punto de venta""",
    "category": "Point Of Sale",
    "version": "14.0.1.1.0",
    "application": False,
    "depends": ["point_of_sale","pos_product_available"],
    "data": ["security/pos_user_restrict.xml",
             "security/ir.model.access.csv",
             "views/data.xml",
             "views/views.xml",
             "views/pos_views.xml",
             "views/pos_discount.xml",
             "views/product_views.xml",
             "views/pos_dataSync_views.xml"
             ],
    "qweb": [
        "static/src/xml/pos.xml",
        "static/src/xml/product.xml",
        "static/src/xml/OrderReceiptLight.xml",
            ],
    "post_load": None,
    "pre_init_hook": None,
    "post_init_hook": None,
    "uninstall_hook": None,
    "auto_install": False,
    "installable": True,
}
