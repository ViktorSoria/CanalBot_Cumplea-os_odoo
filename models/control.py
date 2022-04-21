from odoo import models
from datetime import date
# import keyboard
import logging
#variable que se imprime en terminal o consola solo para identificar
# _log = logging.getLogger("============")


class mensajeFeliz(models.Model):
  #modelo del cual hereda
  _inherit = "res.users"
  
#funcion que se ejecutara en las acciones planificadas en Oddo
  def mensaje_cumple(self):
  
      #busca el canal en el cual posteara el mensaje
      channel_id = self.env.ref("cumple_modulo.canal_cumpleanos") #modelo.id  referencia
      # channel_id = self.env['mail.channel'].search([('name', '=', canal)]) # referencia o busqueda del canal
      #buscara en la bd las personas que cumplan segun su fecha de nacimiento
      busqueda = self.env['hr.employee'].search([('birthday', '=', date.today())])     
      #recorrido de la lista busqueda para el nombre de los que cumplen años
      if len(busqueda) > 1:
        felicitacion =  "<br>╭══• ೋ•✧๑♡๑✧•ೋ •══╮ <br>¡¡¡ Feliz Cumpleaños !!! UwU <br>╰══• ೋ•✧๑♡๑✧•ೋ •══╯ <br><br>¡¡¡ Que tengan un Excelente Día!!!<br><br><b>"    
      else:
        felicitacion =  "<br>╭══• ೋ•✧๑♡๑✧•ೋ •══╮ <br>¡¡¡ Feliz Cumpleaños !!! UwU <br>╰══• ೋ•✧๑♡๑✧•ೋ •══╯ <br><br>¡¡¡ Que tengas un Excelente Día!!!<br><br><b>"    
      for persona in busqueda:     
        felicitacion = felicitacion + "⭐️ " + persona.name + ". <br>"
          #impresion en consola para pruebas
        # _log.info("%s" %felicitacion)
      if len(busqueda) > 0:    
        #impresion en el canal
        channel_id.message_post(body=felicitacion, subtype_xmlid='mail.mt_comment')
      
      
        
      