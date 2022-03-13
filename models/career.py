# -*- coding: utf-8 -*-
import logging
import pdb
from datetime import datetime, timedelta, date, timezone
from typing import List

import odoo
from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class Career(models.Model):
    """Career"""
    _name = 'climbing_gym_school.career'
    _description = 'Career (ICABA)'
    _inherit = ['mail.thread']

    status_selection = [('pending', "Pending"), ('active', "Active"), ('cancel', "Cancelled")]

    name = fields.Char('Name')
    description = fields.Char('Description', compute='_generate_name')
    obs = fields.Text('Observations')
    state = fields.Selection(status_selection, 'Status', default='pending', track_visibility=True)

    course_ids = fields.One2many('climbing_gym_school.course', inverse_name='career_id',
                                 string='Courses', readonly=True)

    @api.multi
    def action_revive(self):
        for _map in self:
            _map.state = 'pending'

    @api.multi
    def action_active(self):
        for _map in self:
            _map.state = 'active'

    @api.multi
    def action_cancel(self):
        for _map in self:
            _map.state = 'cancel'
