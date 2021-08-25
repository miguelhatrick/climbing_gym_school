# -*- coding: utf-8 -*-
import logging
import pdb
from datetime import datetime, timedelta, date, timezone
from typing import List

import odoo
from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class Exam(models.Model):
    """Exam"""
    _name = 'climbing_gym_school.exam'
    _description = 'Exam'
    _inherit = ['mail.thread']

    status_selection = [('pending', "Pending"), ('active', "Active"), ('closed', "Closed"), ('cancel', "Cancelled")]

    name = fields.Char('Name', compute='_generate_name')
    description = fields.Char('Description')
    obs = fields.Text('Observations')

    exam_date = fields.Date("Exam date", required=True, track_visibility=True)

    organizer_id = fields.Many2one('res.partner', string='Student', readonly=False, required=True,
                                   track_visibility=True)

    course_id = fields.Many2one('climbing_gym_school.course', string='Course', required=True, index=True,
                                track_visibility=True)
    state = fields.Selection(status_selection, 'Status', default='pending', track_visibility=True)

    @api.multi
    def action_revive(self):
        for _map in self:
            _map.state = 'pending'

    @api.multi
    def action_approve(self):
        for _map in self:
            _map.state = 'approved'

    @api.multi
    def action_close(self):
        for _map in self:
            _map.state = 'closed'

    @api.multi
    def action_cancel(self):
        for _map in self:
            _map.state = 'cancel'

    def _generate_name(self):
        # pdb.set_trace()
        for _map in self:
            _map.name = "EXAM-%s" % (_map.id if _map.id else '')
