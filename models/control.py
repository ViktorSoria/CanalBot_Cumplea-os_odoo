from odoo import models
from datetime import date
import random
# import logging
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
        #lista de frases en plural
        plural = [
          "<br>╭══• ೋ•✧๑♡๑✧•ೋ •══╮ <br>¡¡¡ Feliz Cumpleaños !!! UwU <br>╰══• ೋ•✧๑♡๑✧•ೋ •══╯ <br><br>¡¡¡ Que tengan un Excelente Día!!!<br><br><b>", 
          "A nombre de toda la empresa les deseamos un cumpleaños muy feliz, los mejores deseos para que gocen de mucha felicidad en sus vidas.<br><b>",
          "Es una dicha el poder trabajar con personas como ustedes, gracias por todo su apoyo, constancia y dedicacion. Que la pasen muy bien en su día, feliz cumpleaños.<br><b>", 
          "Es nuestro deseo que su vida se llene de muchos éxitos y satisfacciones, que al lado de su familia puedan disfrutar de un maravilloso y feliz cumpleaños. Muchos abrazos y saludos de parte de todos.<br><b>",
          "La compañía valora y reconoce la labor que desempeñan, es por eso que deseamos tengan un bonito dia y reciban de parte de todo el equipo un muy feliz cumpleaños.<br><b>", 
          "Hoy queremos expresar a cada uno de los empleados de esta compañía nuestras gracias por ser buenos compañeros y esperamos que nos acompañen mucho tiempo más. Les deseamos mucha felicidad en este día tan especial de su cumpleaños.<br><b>", 
          "A nombre de nuestra gran familia empresarial queremos enviarles un saludo muy especial deseándoles un muy feliz cumpleaños. Que todos sus deseos se hagan realidad.<br><b>",
          "Somos una gran familia empresarial y por eso es motivo de orgullo para nosotros hacerles este pequeño reconocimiento en el día de su cumpleaños. Muchas felicidades.<br><b>",
          "Es un gusto contar con empleados tan leales, honestos y dedicados como ustedes, por eso el día de su cumpleaños les deseamos mil felicidades.<br><b>",
          "Una de las mejores recompensas que podemos tener es el aprecio y la compañía de nuestros compañeros de trabajo, por eso les queremos felicitar en el día de su cumpleaños y desearles muchos éxitos en su vida.<br><b>",
          "Somos una de las mejores compañías en nuestro campo y nada de eso sería posible sin la ayuda de empleados como ustedes, gracias por su compromiso y colaboración. Por eso en el día de su cumpleaños les deseamos muchas felicidades.<br><b>",
          "Gracias por brindarnos esa gran motivación a todos nosotros que nos lleva a ser los mejores. En el día de su cumpleaños les deseamos éxitos y muchas felicitaciones.<br><b>"]
        #ramdom.choice(list) Devuelve un elemento aleatorio de una lista
        felicitacion = random.choice(plural)
      else:
         #lista de frases en singular
        singular = [
          "<br>╭══• ೋ•✧๑♡๑✧•ೋ •══╮ <br>¡¡¡ Feliz Cumpleaños !!! UwU <br>╰══• ೋ•✧๑♡๑✧•ೋ •══╯ <br><br>¡¡¡ Que tengas un Excelente Día!!!<br><br><b>", 
          "A nombre de toda la empresa te deseo un cumpleaños muy feliz, los mejores deseos para que goces de mucha felicidad en tu vida.<br><b>",
          "Es una dicha el poder trabajar con alguien como tú, gracias por todo tu apoyo, constancia y dedicacion. Que la pases muy bien en tu día, feliz cumpleaños.<br><b>", 
          "Es nuestro deseo que tu vida se llene de muchos éxitos y satisfacciones, que al lado de tu familia puedas disfrutar de un maravilloso y feliz cumpleaños. Muchos abrazos y saludos de parte de todos.<br><b>",
          "La compañía valora y reconoce la labor que desempeñas, es por eso que deseamos tengas un bonito dia y recibas de parte de todo el equipo un muy feliz cumpleaños.<br><b>",
          "Hoy queremos expresar a cada uno de los empleados de esta compañía nuestras gracias por ser el buen compañero que es y esperamos que nos acompañe mucho tiempo más. Le deseamos mucha felicidad en este día tan especial de su cumpleaños.<br><b>", 
          "A nombre de nuestra gran familia empresarial queremos enviarle un saludo muy especial deseándole un feliz cumpleaños. Que todos sus deseos se hagan realidad.<br><b>",
          "Somos una gran familia empresarial y por eso es motivo de orgullo para nosotros hacerle este pequeño reconocimiento en el día de su cumpleaños. Muchas felicidades.<br><b>", 
          "Es un gusto contar con empleados tan leales, honestos y dedicados como tú, por eso el día de tu cumpleaños te deseamos mil felicidades.<br><b>", 
          "Una de las mejores recompensas que podemos tener es el aprecio y la compañía de nuestros compañeros de trabajo, por eso te queremos felicitar en el día de tu cumpleaños y desear muchos éxitos en tu vida.<br><b>", 
          "Somos una de las mejores compañías en nuestro campo y nada de eso sería posible sin la ayuda de empleados como usted, gracias por su compromiso y colaboración. Por eso en el día de su cumpleaños le deseamos muchas felicidades.<br><b>", 
          "Gracias por brindarnos esa gran motivación a todos nosotros que nos lleva a ser los mejores. En el día de tu cumpleaños te deseamos éxitos y muchas felicidades.<br><b>"]
         #ramdom.choice(list) Devuelve un elemento aleatorio de una lista
        felicitacion =  random.choice(singular)
        #recorrido de la lista busqueda 
      for persona in busqueda:     
        felicitacion = felicitacion + "⭐️ " + persona.name + ". <br>"
          #impresion en consola para pruebas
        # _log.info("%s" %felicitacion)
      if len(busqueda) > 0:    
        #impresion en el canal si se cumple la condicion de que hay elementos en la lista
        channel_id.message_post(body=felicitacion, subtype_xmlid='mail.mt_comment')
        
      