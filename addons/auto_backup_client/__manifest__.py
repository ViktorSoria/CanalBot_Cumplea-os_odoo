# -*- coding: utf-8 -*-
{
    'name': "Database Auto-Backup Upload",

    'summary': """
        Automatically Upload backup.
        """,

    'description': """
    """,

    'category': 'Generic Modules',

    # any module necessary for this one to work correctly
    'depends': ['base','mail'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/backup_view.xml',
        'data/backup_data.xml',
    ],
}
