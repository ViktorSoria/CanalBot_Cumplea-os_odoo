# -*- coding: utf-8 -*-

#Crea un nuevo modelo que hereda todos los fields de otro modelo, y ademas podemos añadir otro field adicional
from odoo import api, fields, models, _

class ProjectProject(models.Model):
	_inherit= "project.task"			#Hereda de tabla existente (este nombre puede verse en la URL al ingresar al modulo)
	
	user_areas=fields.Many2many('project.project', store=False)
	#user_id = fields.Many2one('res.users', 'Stage Owner', index=True, domain="[('soporte','=',True)]")
	#current_user = fields.Many2one('res.users', default=lambda self: self.env.user) #obtiene el usuario actual


	@api.onchange('user_id')
	def get_user_areas(self): #Recolecta informacion de las areas asignadas al usuario actual (cada vez que se cambia al usuario)
		self.project_id=False #Des-selecciona el area al cambiar el usuario encargado
		self.user_areas=self.user_id.User_Areas_ids if self.user_id else None

class UsersCustom(models.Model):
	_inherit = "res.users"

	soporte = fields.Boolean(string="soporte")
	User_Areas_ids=fields.Many2many('project.project', string="Areas designadas")
	
"""
class Project_kanban(models.Model):
	_inherit= "project.project"	
	
	user_areas=fields.Many2many('project.project', store=False, default = lambda self: self.env.user.User_Areas_ids)

	def get_user_areas(self):
		return self.env.user.User_Areas_ids
"""
	