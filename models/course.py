# -*- coding: utf-8 -*-
import logging
import math
import pdb
from datetime import datetime, timedelta, date, timezone
from typing import List

import pytz

import odoo
from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class Course(models.Model):
    """Courses given"""
    _name = 'climbing_gym_school.course'
    _description = 'Course'
    _inherit = ['mail.thread']
    _rec_name = 'name_long'

    status_selection = [('pending', "Pending"), ('active', "Active"), ('closed', "Closed"), ('cancel', "Cancelled")]

    name = fields.Char('Name', compute='_generate_name')
    name_long = fields.Char('Name long')

    description = fields.Char('Description')
    obs = fields.Text('Observations')

    organizer_id = fields.Many2one('res.partner', string='Course organizer', readonly=False, required=True,
                                   track_visibility=True)

    course_date = fields.Date("Course start", required=False, track_visibility=True)

    inscription_start_date = fields.Date("Registration begin", required=True, track_visibility=True)

    inscription_end_date = fields.Date("Registration end", required=True, track_visibility=True)

    date_tz = fields.Selection('_tz_get', string='Timezone', required=True,
                               default=lambda self: self.env.user.tz or 'UTC')

    career_id = fields.Many2one('climbing_gym_school.career', string='Career', required=False, index=True,
                                track_visibility=True)

    course_type_id = fields.Many2one('climbing_gym_school.course_type', string='Course type', required=True, index=True,
                                     track_visibility=True)

    course_students_ids = fields.One2many('climbing_gym_school.course_student', inverse_name='course_id',
                                          string='Students', readonly=True)

    accepted_course_students_ids = fields.One2many('climbing_gym_school.course_student', string='Accepted students',
                                                   compute='_calculate_accepted_students_ids', readonly=True)

    pending_course_students_ids = fields.One2many('climbing_gym_school.course_student', string='Pending students',
                                                  compute='_calculate_pending_students_ids', readonly=True)

    cancelled_course_students_ids = fields.One2many('climbing_gym_school.course_student', string='Cancelled students',
                                                    compute='_calculate_cancelled_students_ids', readonly=True)

    product_product_ids = fields.Many2many(comodel_name='product.product',
                                           relation='climbing_gym_school_course_prod', column1='course_id',
                                           column2='product_id',
                                           string='Linked products')

    total_spots_qty = fields.Integer(string="Total spots in this course", required=True,
                                     track_visibility=True)

    available_spots_qty = fields.Integer(string="Available spots in this course", readonly=True,
                                         compute='_calculate_available_qty')

    accepted_students_qty = fields.Integer(string="Accepted student qty", readonly=True,
                                           compute='_calculate_accepted_students_qty')

    sold_spots_qty = fields.Integer(string="Sold spots", readonly=True,
                                    compute='_calculate_sold_qty')

    sold_spots_pos_qty = fields.Integer(string="Sold spots though POS", readonly=True,
                                        compute='_calculate_sold_pos_qty')

    sale_order_ids = fields.One2many('sale.order', string="Sale orders", readonly=True,
                                     compute='_calculate_sale_order_ids')

    pos_order_ids = fields.One2many('pos.order', string="Pos orders", readonly=True,
                                    compute='_calculate_pos_order_ids')

    dummy_counter = fields.Integer(string="used to trigger writes")

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

            if _map.inscription_end_date < datetime.now().date():
                raise ValidationError('Registration end date is in the past')

            _map.state = 'active'

    @api.multi
    def action_close(self):
        for _map in self:
            _map.state = 'closed'

    @api.multi
    def action_cancel(self):
        for _map in self:
            _map.state = 'cancel'

    @api.multi
    def action_send_mailing(self):
        """
        This function opens a window to compose an email
        """
        # self.ensure_one()

        # Lets create a new mass mailing
        maailing = self.sudo().env['mail.mass_mailing'].create({
            'name': "Message for attendants of : %s" % (self.description),
            'mailing_model_id': self.env.ref('base.model_res_partner').id,
            'reply_to': self.env.user.email,
            'reply_to_mode': 'email',
            'mailing_domain': [["climbing_gym_school_course_student.course_id.id", "=", self.id]],
            'state': 'draft'
        })

        ctx = {
            'id': maailing.id,
        }

        ret = []
        for _map in self:
            return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'mail.mass_mailing',
                'target': 'new',
                'res_id': maailing.id,
                'context': ctx,
            }

    @api.constrains('inscription_start_date', 'inscription_end_date')
    def _data_check_date(self):
        for _map in self:
            if _map.inscription_end_date < _map.inscription_start_date:
                raise ValidationError('Registration end date must be AFTER registration start date')
            pass

    # @api.constrains('product_product_ids')
    # def _data_check_date(self):
    #    for _map in self:
    #        if len(_map.product_product_ids) < 1:
    #            raise ValidationError('A course must have related products')
    #        else:
    #            pass

    def _generate_name(self):
        for _map in self:
            _map.name = "COURSE-%s" % (_map.id if _map.id else '')

    @api.multi
    def name_get(self):
        res = []
        for rec in self:
            res.append((rec.id, "COURSE-%s %s" % (rec.id if rec.id else '', rec.description)))

        return res

    def _calculate_available_qty(self):
        for _c in self:
            _c.available_spots_qty = _c.total_spots_qty - _c.sold_spots_qty

    def _calculate_accepted_students_ids(self):
        _filter = ['accepted']
        for _c in self:
            _c.accepted_course_students_ids = _c.course_students_ids.search(
                [('course_id', '=', _c.id), ('state', 'in', _filter)])

    def _calculate_pending_students_ids(self):
        _filter = ['pending']
        for _c in self:
            _c.pending_course_students_ids = _c.course_students_ids.search(
                [('course_id', '=', _c.id), ('state', 'in', _filter)])

    def _calculate_cancelled_students_ids(self):
        _filter = ['cancel', 'rejected']
        for _c in self:
            _c.cancelled_course_students_ids = _c.course_students_ids.search(
                [('course_id', '=', _c.id), ('state', 'in', _filter)])

    def _calculate_accepted_students_qty(self):
        for _c in self:
            _c.accepted_students_qty = len(_c.accepted_course_students_ids)

    def _calculate_sold_qty(self):
        """
        Calculate all sales. POS + SaleOrder
        """
        for _c in self:
            _c.sold_spots_qty = sum(map(lambda x: int(x.sales_count), _c.product_product_ids))

    def _calculate_sold_pos_qty(self):
        """
        Calculate to total sales though POS for all products included in this course
        """
        _filter = ['paid', 'done', 'invoiced']
        for _c in self:
            # Search the POS Sales lines by product
            _lines = self.sudo().env['pos.order.line'].search([
                ('product_id', 'in', _c.product_product_ids.ids)
            ])

            # Calculate qty
            _c.sold_spots_pos_qty = sum(map(lambda x: int(x.qty) if x.order_id.state in _filter else 0, _lines))

    def _calculate_sale_order_ids(self):
        """
        Get the sale orders linked to this course
        """

        for _c in self:
            # Search the POS Sales lines by product
            _lines = self.sudo().env['sale.order.line'].search([
                ('product_id', 'in', _c.product_product_ids.ids)
            ])

            _ids = list(map(lambda x: x.order_id.id, _lines))
            _filtered = _ids
            filter(lambda x: _filtered.remove(x) is None and _filtered.count(x) == 0, _ids)

            _c.sale_order_ids = self.sudo().env['sale.order'].browse(list(_filtered))

    def _calculate_pos_order_ids(self):
        """
        Get the sale orders linked to this course
        """

        for _c in self:
            # Search the POS Sales lines by product
            _lines = self.sudo().env['pos.order.line'].search([
                ('product_id', 'in', _c.product_product_ids.ids)
            ])

            _ids = list(map(lambda x: x.order_id.id, _lines))
            _filtered = _ids
            filter(lambda x: _filtered.remove(x) is None and _filtered.count(x) == 0, _ids)

            _c.pos_order_ids = self.sudo().env['pos.order'].browse(list(_filtered))

    @api.model
    def _tz_get(self):
        return [(x, x) for x in pytz.all_timezones]

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
    def current_active_courses(self):
        active_course_ids = self.sudo().env['climbing_gym_school.course'].search([
            ('state', 'in', ['active'])
        ])

    def update_product_availability(self):

        super(Course, self).browse(self.id)._update_product_availability()


    def _update_product_availability(self):
        """
        Updates quantities of the products linked to this course
        """

        # Available is calculated considering POS and SO sales.
        _available = self.available_spots_qty
        _logger.info('Updating course %s availability to %d' % (self.name, _available))

        for prod in self.product_product_ids:

            # Get the POS sale of this product here We need to subtract it from the prod.sales_count
            _lines = self.sudo().env['pos.order.line'].search([
                ('product_id', '=', prod.id)
            ])

            # Calculate POS qty
            _filter = ['paid', 'done', 'invoiced']
            _sold_pos_qty = sum(map(lambda x: int(x.qty) if x.order_id.state in _filter else 0, _lines))

            # Verify Status and date
            _current_date = datetime.now().date()

            if self.state != 'active' or \
                    self.inscription_start_date > _current_date or \
                    self.inscription_end_date < _current_date:
                _logger.info('Course inactive or out of registering date.')
                _new_quantity = float(prod.sales_count - _sold_pos_qty)
            else:
                _new_quantity = float(_available + prod.sales_count - _sold_pos_qty)

            vals = {
                'new_quantity': float(1.0),
                'product_id': prod.id,
                'lot_id': None,
                'location_id': None,
                'partner_id': None
            }

            # Get default location
            scpq = self.sudo().env['stock.change.product.qty_custom']

            vals2 = scpq.default_get(vals)

            vals = {
                'new_quantity': _new_quantity,
                'product_id': prod.id,
                # 'lot_id': None,
                'location_id': vals2["location_id"],
                'partner_id': None
            }

            # Perform the qty update
            product_changer = scpq.create(vals)
            product_changer.change_product_qty()

    @api.model
    def create(self, vals):
        """
        Used to trigger the update function
        :param vals:
        :return:
        """
        result = super(Course, self).create(vals)

        if result:
            result.update_product_availability()

        return result

    @api.multi
    def write(self, vals):
        """
        Used to trigger the update function
        :param vals:
        :return:
        """
        result = super(Course, self).write(vals)

        if result:
            self.update_product_availability()

        return result


    def cron_update_course_status(self):
        _courses_ids = self.sudo().env['climbing_gym_school.course'].search([
            ('state', '=', 'active')
        ])
        current_date = datetime.now().date()
        for _course_id in _courses_ids:

            if _course_id.inscription_end_date < current_date:
                _course_id.action_close()
                continue

            _course_id.update_product_availability()

