# -*- coding: utf-8 -*-

{
    'name': 'credit Payment Acquirer',
    'category': 'Accounting/Payment Acquirers',
    'summary': 'Payment Acquirer: credit Implementation',
    'version': '1.0',
    'description': """credit Payment Acquirer""",
    'depends': ['payment'],
    'data': [
        'views/payment_views.xml',
        'views/payment_credit_templates.xml',
        'data/payment_acquirer_data.xml',
    ],
    'installable': True,
    'auto_install': True,

}
