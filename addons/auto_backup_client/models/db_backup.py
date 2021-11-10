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

    def db_backup(self,kw,active_id,bkp_file):
        name = kw.get('db')
        regis = odoo.registry(name)
        _logger.warning("Creando Respaldo")
        with Environment.manage():
            with regis.cursor() as cr:
                env = Environment(cr, kw.get('uid'), {})
                obj = env['db.backup'].browse(active_id)
                try:
                    dir = env['ir.config_parameter'].get_param("path_backs") or "/tmp/backups"
                    file_path = os.path.join(dir, bkp_file)
                    fp = open(file_path, 'wb')
                    odoo.service.db.dump_db(name, fp, "zip")
                    fp.close()
                    md5 = self.gen_md5(file_path)
                    obj.write({'name': bkp_file,'state':'term','md5':md5})
                except Exception as e:
                    obj.write({'name': bkp_file, 'state': 'error','error':str(e)})
                env.cr.commit()
                _logger.warning("Respaldo Creado")

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

lines = self.env['purchase.order.line'].search([('order_id.state','in',['done','purchase'])])
prod = {}
for l in lines:
    if l.product_id.id in prod:
        if l.l.order_id.date_approve > prod[l.product_id.id][1]:
            prod[l.product_id] = [l.product_id, l.order_id.date_approve, l.price_unit]
    else:
        prod[l.product_id] = [l.product_id,l.order_id.date_approve,l.price_unit]

for p,v in prod.items():
    p.write({'standard_price':v[2]})