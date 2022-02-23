# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class Project(models.Model):
	_inherit = "project.project"

	soporte = fields.Boolean("Soporte", default=True)


class ProjectTask(models.Model):
	_inherit= "project.task"			#Hereda de tabla existente (este nombre puede verse en la URL al ingresar al modulo)
	
	user_areas=fields.Many2many('project.project', store=False) #Areas designadas al usuario actual
	usuarios_filtrados=fields.Many2many('res.users', store=False) #Usuarios designados al area actualmente puesta

	@api.onchange('user_id')
	def get_user_areas(self): #Recolecta informacion de las areas asignadas al usuario actual (cada vez que se cambia al usuario)
		self.user_areas=self.user_id.User_Areas_ids if self.user_id else None


	@api.onchange('project_id') #Obtiene los usuarios relacionados con el area
	def get_users(self): 
		self.user_id=False #Des-selecciona el usuario al cambiar el area
		if self.project_id: #Si hay algun area definida
			usuarios_soporte_area=self.env['res.users'].search([('soporte', '=', True)]) #obtiene los usuarios de soporte
			self.usuarios_filtrados=usuarios_soporte_area.filtered(lambda x: self.project_id.id in x.User_Areas_ids.ids) #Filtra los usuarios que pertenecen al area actual


class UsersCustom(models.Model):
	_inherit = "res.users"

	soporte = fields.Boolean(string="soporte")
	User_Areas_ids=fields.Many2many('project.project', string="Areas designadas")