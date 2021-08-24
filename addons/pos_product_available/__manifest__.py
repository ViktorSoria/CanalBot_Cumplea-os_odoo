{
    "name": """POS: show product qty""",
    "summary": """Adds available quantity at products in POS""",
    "category": "Point Of Sale",
    "images": ["images/pos_product_available.jpg"],
    "version": "14.0.1.1.0",
    "application": False,
    "license": "Other OSI approved licence",  # MIT
    "depends": ["point_of_sale", "stock",'l10n_mx_edi'],
    "external_dependencies": {"python": [], "bin": []},
    "data": ["data.xml", "views/views.xml"],
    "qweb": ["static/src/xml/pos.xml"],
    "post_load": None,
    "pre_init_hook": None,
    "post_init_hook": None,
    "uninstall_hook": None,
    "auto_install": False,
    "installable": True,
}
