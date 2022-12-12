# -*- coding: utf-8 -*-
import logging
import pdb
from datetime import datetime, timedelta, date, timezone
from typing import List

import pytz

import odoo
from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class Exam(models.Model):
    """Exam"""
    _name = 'climbing_gym_school.exam'
    _description = 'Exam'
    _inherit = ['mail.thread']

    status_selection = [('pending', "Pending"), ('closed', "Closed"), ('cancel', "Cancelled")]

    name = fields.Char('Name', compute='_generate_name')
    description = fields.Char('Description')
    obs = fields.Text('Observations')

    exam_date = fields.Date("Exam date", required=True, track_visibility=True)

    date_tz = fields.Selection('_tz_get', string='Timezone', required=True,
                               default=lambda self: self.env.user.tz or 'UTC')

    exam_students_count = fields.Integer(compute='_compute_exam_students_count')

    exam_students_ids = fields.One2many('climbing_gym_school.exam_student', inverse_name='exam_id',
                                        string='Students', readonly=True)

    organizer_id = fields.Many2one('res.partner', string='Exam organizer', readonly=False, required=True,
                                   track_visibility=True)

    course_id = fields.Many2one('climbing_gym_school.course', string='Course', required=True, index=True,
                                track_visibility=True)
    state = fields.Selection(status_selection, 'Status', default='pending', track_visibility=True)

    pending_students_ids = fields.One2many('climbing_gym_school.exam_student', string='Pending students',
                                           compute='_calculate_pending_students_ids', readonly=True)

    approved_students_ids = fields.One2many('climbing_gym_school.exam_student', string='Approved students',
                                            compute='_calculate_approved_students_ids', readonly=True)

    failed_students_ids = fields.One2many('climbing_gym_school.exam_student', string='Failed students',
                                          compute='_calculate_failed_students_ids', readonly=True)

    @api.model
    def _tz_get(self):
        return [(x, x) for x in pytz.all_timezones]

    @api.multi
    def action_revive(self):
        for _map in self:
            _map.state = 'pending'

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

    def _calculate_approved_students_ids(self):
        _filter = ['approved']
        for _c in self:
            _c.approved_students_ids = _c.exam_students_ids.search(
                [('exam_id', '=', _c.id), ('state', 'in', _filter)])

    def _calculate_failed_students_ids(self):
        _filter = ['failed']
        for _c in self:
            _c.failed_students_ids = _c.exam_students_ids.search(
                [('exam_id', '=', _c.id), ('state', 'in', _filter)])

    def _calculate_pending_students_ids(self):
        _filter = ['pending']
        for _c in self:
            _c.pending_students_ids = _c.exam_students_ids.search(
                [('exam_id', '=', _c.id), ('state', 'in', _filter)])

    @api.multi
    def action_approve_all(self):

        for _c in self:
            for student in _c.exam_students_ids:
                student.action_approve()

    @api.multi
    def _compute_exam_students_count(self):
        for record in self:
            record.exam_students_count = self.env['climbing_gym_school.exam_student'].search_count(
                [('exam_id', '=', self.id)])

    def action_open_view_exam_students(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Exam students',
            'view_mode': 'tree,form',
            'res_model': 'climbing_gym_school.exam_student',
            'domain': [('exam_id', '=', self.id)],
            # 'context': "{'create': False}"
        }
