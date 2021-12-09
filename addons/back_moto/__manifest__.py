
{
    "name": """Back Moto""",
    "summary": """Acondicionamineto Motopartes""",
    "version": "14.0",
    "application": False,
    "depends": ["purchase","sale",'crm','account_edi'],
    "data": ["security/security.xml",
             "security/ir.model.access.csv",
             "views/assets.xml",
             "views/purchase_views.xml",
             "views/product_view.xml",
             "views/pricelist_views.xml",
             "views/report_view.xml",
             "report/report.xml",
             "views/global_invoice_view.xml",
             ],
}
