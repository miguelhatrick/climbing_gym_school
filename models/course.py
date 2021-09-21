# -*- coding: utf-8 -*-
import logging
import pdb
from datetime import datetime, timedelta, date, timezone
from typing import List

import odoo
from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class Course(models.Model):
    """Courses given"""
    _name = 'climbing_gym_school.course'
    _description = 'Course'
    _inherit = ['mail.thread']

    status_selection = [('pending', "Pending"), ('active', "Active"), ('closed', "Closed"), ('cancel', "Cancelled")]

    name = fields.Char('Name', compute='_generate_name')
    description = fields.Char('Description')
    obs = fields.Text('Observations')

    organizer_id = fields.Many2one('res.partner', string='Course organizer', readonly=False, required=True,
                                   track_visibility=True)

    course_date = fields.Date("Course date", required=False, track_visibility=True)

    career_id = fields.Many2one('climbing_gym_school.career', string='Career', required=False, index=True,
                                track_visibility=True)

    course_type_id = fields.Many2one('climbing_gym_school.course_type', string='Course type', required=True, index=True,
                                     track_visibility=True)

    course_students_ids = fields.One2many('climbing_gym_school.course_student', inverse_name='course_id',
                                          string='Students', readonly=True)

    product_product_ids = fields.Many2many(comodel_name='product.product',
                                           relation='climbing_gym_school_course_prod', column1='course_id',
                                           column2='product_id',
                                           string='Linked products')

    total_spots = fields.Integer(string="Total spots in this course")

    available_spots = fields.Integer(string="Available spots in this course", readonly=True,
                                     compute='_calculate_available')

    state = fields.Selection(status_selection, 'Status', default='pending', track_visibility=True)

    def _compute_website_url(self):
        for blog_post in self:
            blog_post.website_url = "/courses/%s" % blog_post.id

    @api.multi
    def action_revive(self):
        for _map in self:
            _map.state = 'pending'

    @api.multi
    def action_active(self):
        for _map in self:
            _map.state = 'active'

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
            _map.name = "COURSE-%s" % (_map.id if _map.id else '')

    def _calculate_available(self):
        for _c in self:
            _c.available_spots = _c.total_spots - _c.course_students_ids.search_count(
                [('state', 'in', ['accepted']), ('course_id', '=', _c.id)])

    def is_student_registered(self, partner_id):
        """
        Control if a partner is registered in the course
        :param partner_id: res.partner
        :return: course_student
        """
        register = [d for d in self.course_students_ids if d.partner_id == partner_id]

        if len(register) == 1:
            return register[0]
        return None

    # TODO: is this used?
    @staticmethod
    def current_active_courses():

        active_course_ids = self.sudo().env['climbing_gym_school.course'].search([
            ('state', 'in', ['active'])
        ])
