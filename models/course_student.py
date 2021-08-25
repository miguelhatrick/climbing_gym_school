# -*- coding: utf-8 -*-
import logging
import pdb
from datetime import datetime, timedelta, date, timezone
from typing import List

import odoo
from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class CourseStudent(models.Model):
    """Career"""
    _name = 'climbing_gym_school.course_student'
    _description = 'Student registration into a course'
    _inherit = ['mail.thread']

    status_selection = [('pending', "Pending"), ('accepted', "Accepted"), ('rejected', "Rejected")]

    name = fields.Char('Name', compute='_generate_name')
    obs = fields.Text('Observations')

    student_id = fields.Many2one('res.partner', string='Student', readonly=False, required=True,
                                   track_visibility=True)

    course_id = fields.Many2one('climbing_gym_school.course', string='Course', required=False, index=True,
                                track_visibility=True)

    state = fields.Selection(status_selection, 'Status', default='pending', track_visibility=True)

    @api.multi
    def action_revive(self):
        for _map in self:
            _map.state = 'pending'

    @api.multi
    def action_accept(self):
        for _map in self:
            _map.state = 'accepted'

    @api.multi
    def action_reject(self):
        for _map in self:
            _map.state = 'rejected'

    def _generate_name(self):
        # pdb.set_trace()
        for _map in self:
            _map.name = "COUR-ST-%s" % (_map.id if _map.id else '')
