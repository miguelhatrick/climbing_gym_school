# -*- coding: utf-8 -*-
import logging
import pdb
from datetime import datetime, timedelta, date, timezone
from typing import List

import odoo
from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ExamStudent(models.Model):
    """Exam result of each student"""
    _name = 'climbing_gym_school.exam_student'
    _description = 'Exam student result'
    _inherit = ['mail.thread']

    status_selection = [('pending', "Pending"), ('approved', "Approved"), ('rejected', "Rejected")]

    name = fields.Char('Name', compute='_generate_name')
    obs = fields.Text('Observations')

    grade = fields.Integer('Grade')

    partner_id = fields.Many2one('res.partner', string='Student', readonly=False, required=True,
                                 track_visibility=True)
    exam_id = fields.Many2one('climbing_gym_school.exam', string='Exam', required=True, index=True,
                              track_visibility=True)

    course_id = fields.Many2one('climbing_gym_school.course', string='Course', compute='_get_course_id')

    state = fields.Selection(status_selection, 'Status', default='pending', track_visibility=True)

    @api.onchange('exam_id')
    def on_change_exam(self):
        # self._get_course()
        # self._get_course_type()
        pass

    @api.multi
    def write(self, vals):
        result = super(ExamStudent, self).write(vals)
        return result

    @api.multi
    def action_revive(self):
        for _map in self:
            _map.state = 'pending'

    @api.multi
    def action_approve(self):
        for _map in self:
            _map.state = 'approved'

    @api.multi
    def action_reject(self):
        for _map in self:
            _map.state = 'rejected'

    def _generate_name(self):
        # pdb.set_trace()
        for _map in self:
            _map.name = "EXAM-ST-%s" % (_map.id or '')

    def _get_course_id(self):
        for _map in self:
            _map.course_id = _map.exam_id.course_id if _map.exam_id else None
