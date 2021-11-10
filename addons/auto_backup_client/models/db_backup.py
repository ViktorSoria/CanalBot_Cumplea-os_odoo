# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _,sql_db,SUPERUSER_ID
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
    md5 = fields.Char("Suma Binaria")


    @api.model
    def cron_delete_back(self):
        days = self.env['ir.config_parameter'].get_param("days_delete") or 7
        max = self.env['ir.config_parameter'].get_param("max_back") or 1
        max = int(max)
        days = int(days)
        backs = self.search([('delete','=',False),('delete_date','<',datetime.now()-timedelta(days=days))])
        old = self.search([('delete', '=', False)],order="create_date desc")
        old = old - old[:max]
        backs = backs + old
        backs.delete_back()

    def delete_back(self):
        dir = self.env['ir.config_parameter'].get_param("path_backs") or "/tmp/backups"
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

    def db_backup(self):
        try:
            dir = self.env['ir.config_parameter'].get_param("path_backs") or "/tmp/backups"
            file_path = os.path.join(dir, self.name)
            fp = open(file_path, 'wb')
            odoo.service.db.dump_db(self.env.cr.dbname, fp, "zip")
            fp.close()
            md5 = self.gen_md5(file_path)
            self.write({'state': 'term', 'md5': md5})
            _logger.warning("Termino respaldo")
        except Exception as e:
            self.write({'state': 'error', 'error': str(e)})
            _logger.warning(str(e))
        _logger.warning("Respaldo Creado")

    def db_backup_thr(self,kw,active_id,bkp_file):
        name = kw.get('db')
        regis = odoo.registry(name)
        _logger.warning("Creando Respaldo")
        with Environment.manage():
            with regis.cursor() as cr:
                env = Environment(cr, kw.get('uid'), {})
                obj = env['db.backup'].browse(active_id)
                obj.db_backup()
                env.cr.commit()
        _logger.warning("Saliendo ambiente")

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
        vals['name'] = str_tok
        back = self.create(vals)
        _thread = threading.Thread(target=back.db_backup_thr, args=({'db':name, 'uid':SUPERUSER_ID},back.id,str_tok))
        _thread.start()
        return token

    def download(self):
        self.write({'state':'des','date_down':datetime.now()})

    @api.model
    def action_model(self,token,action):
        obj = self.search([('token','=',token)])
        if action == 'delete':
            obj.delete_back()
        elif action == 'download':
            obj.download()
        return True

    def gen_md5(self,fname):
        hash_md5 = hashlib.md5()
        f = open(fname, "rb")
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
        return hash_md5.hexdigest()