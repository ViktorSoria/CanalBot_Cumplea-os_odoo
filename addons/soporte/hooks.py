from odoo import api, SUPERUSER_ID
import logging
_log = logging.getLogger("Soporte (%s) -------> " % __name__)


def test_post_init_hook(cr, registry):
	"ejecucion despues de intalado el modulo"
	env=api.Environment(cr, SUPERUSER_ID,{})

	#acciones_ventana = env['ir.actions.act_window']
	_log.info("**************************************")

	menu_principal_area=env.ref("project.open_view_project_all") #obtengo la accion(objeto)
	menu_principal_area.write({'name':"Area2"})

	_log.info(menu_principal_area)

	env.cr.commit()
