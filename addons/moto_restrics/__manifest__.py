{
    "name": "Restricciones multimoto",
    "summary": "Módulo con algunas restricciones y permisos para el back office de multimoto.",
    "author": "Tekniu: Isaac",
    "depends": [
        "base", "account", "account_edi", "point_of_sale"
    ],
    "installable": True,
    "data": [
        'security/ir.model.access.csv',
        'views/account_move.xml',
        'views/pos.xml',
        'wizard/pin_auth_wizard.xml',
    ],
    "qweb": [
    ],
}
