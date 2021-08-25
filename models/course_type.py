# -*- coding: utf-8 -*-
import logging
import pdb
from datetime import datetime, timedelta, date, timezone
from typing import List

import odoo
from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class CourseType(models.Model):
    """Course type"""
    _name = 'climbing_gym_school.course_type'
    _description = 'Course Type'
    _inherit = ['mail.thread']

    status_selection = [('pending', "Pending"), ('active', "Active"), ('cancel', "Cancelled")]

    name = fields.Char('Name')
    description  = fields.Char('Description')
    obs = fields.Text('Observations')
    career_id = fields.Many2one('climbing_gym_school.career', string='Career', required=False, index=True,
                                track_visibility=True)
    state = fields.Selection(status_selection, 'Status', default='pending', track_visibility=True)

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
