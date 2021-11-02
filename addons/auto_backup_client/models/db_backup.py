# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _,sql_db
from odoo.api import Environment
import odoo
import pytz
import logging
import threading
import hashlib
import hmac
_logger = logging.getLogger(__name__)

import os
from datetime import datetime,timedelta

try:
    from xmlrpc import client as xmlrpclib
except ImportError:
    import xmlrpclib
import socket


def execute(connector, method, *args):
    res = False
    try:
        res = getattr(connector, method)(*args)
    except socket.error as error:
        _logger.critical('Error while executing the method "execute". Error: ' + str(error))
        raise error
    return res


class DbBackup(models.Model):
    _name = 'db.backup'
    _description = 'Backup configuration record'

    name = fields.Char("Nombre")
    token = fields.Char("Identificador")
    state = fields.Selection([('process','En Proceso'),('term','Generado'),('des','Descargado'),('error','Error')],string="Estado")
    delete = fields.Boolean("Eliminado local")
    delete_date = fields.Datetime("Fecha de Eliminacion")
    date_down = fields.Datetime("Fecha de descarga")
    error = fields.Char("Error")


    @api.model
    def cron_delete_back(self):
        days = self.env['ir.config_parameter'].get_param("days delete") or 7
        days = int(days)
        backs = self.search([('delete','=',False),('create_date','<',datetime.now()-timedelta(days=days))])
        backs.delete_back()

    def delete_back(self):
        dir = "/tmp/backups"
        list_dir = os.listdir(dir)
        date_now = datetime.now()
        for back in self:
            try:
                if back.name in list_dir:
                    fullpath = os.path.join(dir, back.name)
                    os.remove(fullpath)
                back.write({'delete':True,'delete_date':date_now})
            except Exception as e:
                _logger.warning(e)
                back.write({'error': str(e)})

    def db_backup(self,kw,active_id,bkp_file):
        name = kw.get('db')
        new_cr = sql_db.db_connect(name).cursor()
        with Environment.manage():
            env = Environment(new_cr, kw.get('uid'), {})
            obj = env['db.backup'].browse(active_id)
            try:
                file_path = os.path.join("/tmp/backups", bkp_file)
                fp = open(file_path, 'wb')
                odoo.service.db.dump_db(name, fp, "zip")
                fp.close()
                obj.write({'name': bkp_file,'state':'term'})
            except Exception as e:
                obj.write({'name': bkp_file, 'state': 'error','error':str(e)})
            env.cr.commit()
            env.cr.close()

    @api.model
    def create_back(self, vals=None):
        if vals is None:
            vals = {}
        secret = self.env['ir.config_parameter'].sudo().get_param('database.secret')
        name = self.env.cr.dbname
        user_tz = pytz.timezone(self.env.user.tz)
        date_today = pytz.utc.localize(datetime.today()).astimezone(user_tz)
        str_tok = '%s_%s.%s' % (name, date_today.strftime('%Y-%m-%d_%H_%M_%S'), "zip")
        token = hmac.new(secret.encode('utf-8'), str_tok.encode('utf-8'), hashlib.sha256).hexdigest()
        vals['state'] = "process"
        vals['token'] = token
        back = self.create(vals)
        _thread = threading.Thread(target=back.db_backup, args=({'db':name, 'uid':self.env.user.id},back.id,str_tok))
        _thread.start()
        return token

    def download(self):
        self.write({'state':'des','date_down':datetime.now()})