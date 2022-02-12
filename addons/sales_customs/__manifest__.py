{
    "name": "Customización de ventas",
    "summary": "Módulo con customizaciones de lo relacionado con ventas",
    "author": "Tekniu: Isaac, Jehosafat",
    "depends": [
        "base", "point_of_sale", "account", "pos_pay_control", "sale_stock", "stock", "sale", "sale_management", "purchase","l10n_mx_edi"
    ],
    "installable": True,
    "data": [
        'data/assets.xml',
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/pos_order_views.xml',
        'views/account_payment_views.xml',
        'views/orders_views.xml',
        'views/account_report_inherit.xml',
        'report/sale_report.xml',
    ],
    "qweb": [
        "base", "point_of_sale", "pos_pay_control"
    ],
}
