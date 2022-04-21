{
    'name': "Cumpleaños-ChatBot",
    'version': '1.0',
    'depends': ['base'],
    'author': "Tekniu - Victor Soria",
    'website': 'https://soluciones.tekniu.mx/',
    'category': 'Recursos Humanos',
    'summary': "Enviara Felicitar a los empleados mediante Canal Odoo",
    'description': """Cumpleaños Empleados......""",
    'license': 'LGPL-3',
    'demo': [], 
    # data files always loaded at installation
    'data': [        
        "data/canal.xml",
        "data/cron_ir.xml",
    ],
   'installable': True,
    'Application': True,
    'Auto_install': True,
    
}
