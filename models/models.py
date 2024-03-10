# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo import _
import datetime
import logging
import re


_logger = logging.getLogger(__name__) #Información que obtiene del fichero de configuración

class developer(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    is_dev = fields.Boolean()
    access_code = fields.Char()
    
    technologies = fields.Many2many('manage.technology',
                                    relation='developer_technologies',
                                    column1='developer_id',
                                    column2='technologies_id')
    
    tasks = fields.Many2many('manage.task',
                                    relation='developer_tasks',
                                    column1='developer_id',
                                    column2='task_id')
 
    bugs = fields.Many2many('manage.bug',
                                    relation='developer_bugs',
                                    column1='developer_id',
                                    column2='bug_id')
    
    
    improvements = fields.Many2many('manage.improvement',
                                    relation='developer_improvements',
                                    column1='developer_id',
                                    column2='improvement_id')
    

    @api.constrains('access_code')
    def _check_code(self):
        regex = re.compile('^[0-9]{8}[a-z]', re.I)
        for dev in self:
            if regex.match(dev.access_code):
                _logger.info('Código de acceso generado correctamente')
            else:
                raise ValidationError('Formato de código de acceso incorrecto')
            
    _sql_constraints = [('access_code_unique', 'unique(access_code)', 'Access code ya existente.')]

    
    @api.onchange('is_dev')
    def _onchange_is_dev(self):
        categories = self.env['res.partner.category'].search([('name','=','Devs')])
        if len(categories) > 0:
            category = categories[0]
        else:
            category = self.env['res.partner.category'].create({'name':'Devs'})
        self.category_id = [(4, category.id)]    
    

class project(models.Model):
    _name = 'manage.project'
    _description = 'manage.project'
    
    name = fields.Char()
    description = fields.Text()
    histories = fields.One2many(comodel_name="manage.history", inverse_name="project")

class history(models.Model):
    _name = 'manage.history'
    _description = 'manage.history'
    
    name = fields.Char()
    description = fields.Text()
    project = fields.Many2one("manage.project", ondelete="set null")
    tasks = fields.One2many(string="Tareas", comodel_name="manage.task", inverse_name="history")
    used_technologies = fields.Many2many("manage.technology", compute="_get_used_technologies")

    def _get_used_technologies(self):
        for history in self:
            technologies = None
            for task in history.tasks:
                if not technologies:
                    technologies = task.technologies
                else:
                    technologies = technologies + task.technologies
            history.used_technologies = technologies   


class task(models.Model):
    _name = 'manage.task'
    _description = 'manage.task'

    definition_date = fields.Datetime(default=lambda p: datetime.datetime.now())
    project = fields.Many2one('manage.project', related='history.project', readonly=True)
    code = fields.Char(compute="_get_code")
    name = fields.Char(string="Nombre", readonly=False, required=True, help="Introduzca el nombre") #Name
    history = fields.Many2one("manage.history", ondelete="set null", help="Historia relacionada")
    description = fields.Text()
    start_date = fields.Datetime()
    end_date = fields.Datetime()
    is_paused = fields.Boolean()
    sprint = fields.Many2one("manage.sprint", compute="_get_sprint", store=True)
    technologies = fields.Many2many(comodel_name="manage.technology",
                                    relation="technologies_tasks",
                                    column1="task_id",
                                    column2="technology_id")

    #@api.one
    def _get_code(self):
        for task in self:
            try:
                task.code = "TSK_"+str(task.id)
                _logger.info("Código generado: "+task.code)
            except:
                raise ValidationError(_("Generación de código errónea"))
            
    @api.depends('code')
    def _get_sprint(self):
        for task in self:
            # sprints = self.env['manage.sprint'].search([('project.id', '=', task.history.project.id)])
            if isinstance(task.history.project.id, models.NewId):
                id_project = int(task.history.project.id.origin)
            else:
                id_project = task.history.project.id
            sprints = self.env['manage.sprint'].search([('project.id','=', id_project)])
            found = False
            for sprint in sprints:
                if isinstance(sprint.end_date, datetime.datetime) and sprint.end_date > datetime.datetime.now():
                    task.sprint = sprint.id
                    found = True
            if not found:
                task.sprint = False

    def _get_default_dev(self):
        dev = self.browse(self._context.get('current_developer'))
        if dev:
            return [dev.id]
        else:
            return []

    developers = fields.Many2many(comodel_name='res.partner',
                                  relation='developers_tasks',
                                  column1='task_id',
                                  column2='developer_id',
                                  default=_get_default_dev)

class bug(models.Model):
    _name = 'manage.bug'
    _description = 'manage.bug'
    _inherit = 'manage.task'

    technologies = fields.Many2many(comodel_name="manage.technology",
                                    relation="technologies_bugs",
                                    column1="bug_id",
                                    column2="technology_id")
    
    tasks_linked = fields.Many2many(comodel_name="manage.task",
                                    relation="tasks_bugs",
                                    column1="bug_id",
                                    column2="task_id")
    
    bugs_linked = fields.Many2many(comodel_name="manage.bug",
                                    relation="bugs_bugs",
                                    column1="bug1_id",
                                    column2="bug2_id")
    
    improvements_linked = fields.Many2many(comodel_name="manage.improvement",
                                    relation="improvements_bugs",
                                    column1="bug_id",
                                    column2="improvement_id")
    

    developers = fields.Many2many(comodel_name="res.partner",
                                    relation="developers_bugs",
                                    column1="bug_id",
                                    column2="developer_id")

class improvement(models.Model):
    _name = 'manage.improvement'
    _description = 'manage.improvement'
    _inherit = 'manage.task'

    technologies = fields.Many2many(comodel_name="manage.technology",
                                    relation="technologies_improvements",
                                    column1="improvement_id",
                                    column2="technology_id")
    
    histories_linked = fields.Many2many('manage.history')

    developers = fields.Many2many(comodel_name="res.partner",
                                    relation="developers_improvements",
                                    column1="improvement_id",
                                    column2="developer_id")


class sprint(models.Model):
    _name = 'manage.sprint'
    _description = 'manage.sprint'

    project = fields.Many2one("manage.project")
    name = fields.Char()
    description = fields.Text()

    duration = fields.Integer(default=15)
    
    start_date = fields.Datetime()
    end_date = fields.Datetime(compute="_get_end_date", store=True)
    tasks = fields.One2many(string="Tareas", comodel_name="manage.task", inverse_name='sprint')
    
    @api.depends('start_date', 'duration')
    def _get_end_date(self):
        for sprint in self:
            try:
                if isinstance(sprint.start_date, datetime.datetime) and sprint.duration > 0:
                    sprint.end_date = sprint.start_date + datetime.timedelta(days=sprint.duration)
                else:
                    sprint.end_date = sprint.start_date
                _logger.debug("Fecha final de sprint creada")
            except:
                raise ValidationError(_("Generación de fecha errónea"))

class technology(models.Model):
    _name = 'manage.technology'
    _description = 'manage.technology'

    name = fields.Char()
    description = fields.Text()

    photo = fields.Image(max_width=200, max_height=200)
    tasks = fields.Many2many(comodel_name="manage.task",
                             relation="technologies_tasks",
                             column1="technology_id",
                             column2="task_id")


class cliente(models.Model):
    _name = 'nutrete.cliente'
    _description = 'nutrete.cliente'
    
    dni = fields.Char()
    nombre = fields.Char()
    apellidos = fields.Char()
    foto = fields.Image(max_width=200, max_height=200)
    altura = fields.Integer()
    peso = fields.Integer()
    imc = fields.Integer(compute="_calc_imc")
    historial = fields.Text()
    motivoConsulta = fields.Text()
    dietas = fields.One2many(string="Dietas", comodel_name="nutrete.dieta", inverse_name="cliente")

    def _calc_imc(self):
        for cliente in self:
            try:
                cliente.imc = cliente.peso / Math.pow(cliente.altura, 2)
                _logger.info("Cálculo de imc exitoso")
            except:
                raise ValidationError(_("Cálculo de imc erróneo"))

    @api.constrains('dni')
    def _check_dni(self):
        regex = re.compile('^[0-9]{8}[a-z]', re.I)
        for cliente in self:
            if regex.match(cliente.dni):
                _logger.info('DNI con formato correcto')
            else:
                raise ValidationError('Formato de DNI incorrecto')
            
    _sql_constraints = [('dni_unique', 'unique(dni)', 'DNI ya registrado.')]



class dietista(models.Model):
    _name = 'nutrete.dietista'
    _description = 'nutrete.dietista'
    
    dni = fields.Char()
    nombre = fields.Char()
    apellidos = fields.Char()
    foto = fields.Image(max_width=200, max_height=200)
    especialidad = fields.Char()
    talleres = fields.One2many(string="Talleres", comodel_name="nutrete.taller", inverse_name="profesional")
    dietas = fields.One2many(string="Dietas", comodel_name="nutrete.dieta", inverse_name="profesional")
    

class nutricionista(models.Model):
    _name = 'nutrete.nutricionista'
    _description = 'nutrete.nutricionista'
    
    dni = fields.Char()
    nombre = fields.Char()
    apellidos = fields.Char()
    foto = fields.Image(max_width=200, max_height=200)
    especialidad = fields.Char()
    talleres = fields.One2many(string="Talleres", comodel_name="nutrete.taller", inverse_name="profesional")
    dietas = fields.One2many(string="Dietas", comodel_name="nutrete.dieta", inverse_name="profesional")


class dieta(models.Model):
    _name = 'nutrete.dieta'
    _description = 'nutrete.dieta'
    
    cliente = fields.Many2one("nutrete.cliente", ondelete="set null")
    profesional = fields.Many2one("nutrete.nutricionista")
    fecha_registro = fields.Datetime(default=lambda p: datetime.datetime.now())
    fecha_comienzo = fields.Datetime()
    duracion = fields.Integer(default=120)
    fecha_final = fields.Datetime(compute="_get_fecha_final", store=True)
    revisiones = fields.One2many(string="Revisiones", comodel_name="nutrete.revision", inverse_name="dieta")

    @api.depends('fecha_comienzo', 'duracion')
    def _get_fecha_final(self):
        for dieta in self:
            try:
                if isinstance(dieta.fecha_comienzo, datetime.datetime) and dieta.duracion > 0:
                    dieta.fecha_final = dieta.fecha_comienzo + datetime.timedelta(days=dieta.duracion)
                else:
                    dieta.fecha_final = dieta.fecha_comienzo
                _logger.debug("Fecha final de dieta creada")
            except:
                raise ValidationError(_("Generación de fecha errónea"))


class revision(models.Model):
    _name = 'manage.project'
    _description = 'manage.project'
    
    fecha_registro = fields.datetime()
    peso = fields.Integer()
    comentario_cliente = fields.Text()
    evolucion = fields.Char()
    dieta = fields.Many2one("nutrete.dieta", ondelete="set null")
    cliente = tal, aquí iba lo de relacionar revision con dieta con cliente
    profesional = fields.Many2one("nutrete.nutricionista", ondelete="set null")

    def _get_cliente(self):
        for revision in self:
            cliente = None
            for task in revision.tasks:
                if not technologies:
                    technologies = task.technologies
                else:
                    technologies = technologies + task.technologies
            history.used_technologies = technologies


class taller(models.Model):
    _name = 'manage.project'
    _description = 'manage.project'
    
    fecha = fields.Datetime()
    link = fields.Char()
    tema = fields.Char()
    duracion = fields.Integer(default=60)
    profesional = fields.Many2one("nutrete.nutricionista", ondelete="set null")