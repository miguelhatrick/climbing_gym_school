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

    status_selection = [('pending', "Pending"), ('accepted', "Accepted"), ('rejected', "Rejected"),
                        ('cancel', "Cancelled")]

    name = fields.Char('Name', compute='_generate_name')
    obs = fields.Text('Observations')

    partner_id = fields.Many2one('res.partner', string='Student', readonly=False, required=True,
                                 track_visibility=True)

    course_id = fields.Many2one('climbing_gym_school.course', string='Course', required=True, index=True,
                                track_visibility=True)

    course_description = fields.Char(string='Course description', related='course_id.description')

    product = fields.Many2one('product.product', string='Purchased product')
    sale_order = fields.Many2one('sale.order', compute='_get_sale_order')
    sale_order_line = fields.Many2one('sale.order.line', string='Linked Sale order line')
    pos_order = fields.Many2one('pos.order', string='POS order', compute='_get_pos_order')
    pos_order_line = fields.Many2one('pos.order.line', string='Linked POS order line')

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

    @api.multi
    def action_cancel(self):
        for _map in self:
            _map.state = 'cancel'

    def _generate_name(self):
        # pdb.set_trace()
        for _map in self:
            _map.name = "COUR-ST-%s" % (_map.id if _map.id else '')

    @api.constrains('partner_id')
    def _check_unique(self):

        if self.course_id is None:
            pass

        if self.course_id.is_student_registered(self.partner_id) != self:
            raise ValidationError('Can\'t register twice for the same course')

        pass

    def _get_sale_order(self):
        for _map in self:
            _map.sale_order = _map.sale_order_line.order_id if _map.sale_order_line is not False else False

    def _get_pos_order(self):
        for _map in self:
            _map.pos_order = _map.pos_order_line.order_id if _map.pos_order_line is not False else False

    @staticmethod
    def create_or_confirm_course_registration(self, sale_line, course_id):
        # pdb.set_trace()

        sale_order_line = False
        pos_order_line = False
        partner_id = False
        product_id = False

        if isinstance(sale_line, type(self.sudo().env['sale.order.line'])):
            _logger.info('ORIGIN: Sale Order Line %d' % sale_line.id)
            sale_order_line = sale_line
            pos_order_line = False
            partner_id = sale_line.order_id.partner_id
            product_id = sale_line.product_id

        if isinstance(sale_line, type(self.sudo().env['pos.order.line'])):
            _logger.info('ORIGIN: POS Order Line %d' % sale_line.id)
            sale_order_line = False
            pos_order_line = sale_line
            partner_id = sale_line.order_id.partner_id
            product_id = sale_line.product_id

        if partner_id is None or len(partner_id) == 0:
            # create Ticket and return
            _ticket_values = {
                'company_id': None,
                'category_id': self.env['helpdesk.ticket.category'].sudo().search(
                    [('name', '=', 'Membresías / Cuotas')]).id,

                'partner_name': "Unknown",
                'partner_email': "Unknown",

                'description': "No partner selected for purchase on POS - %s" % pos_order_line.order_id,
                'name': 'No active course!',
                'attachment_ids': False,
                'channel_id': self.env['helpdesk.ticket.channel'].sudo().search([('name', '=', 'Web')]).id,
                'partner_id': None,
                'team_id': self.env['helpdesk.ticket.team'].sudo().search([('name', '=', 'Secretaria')]).id,
            }
            new_ticket = self.env['helpdesk.ticket'].sudo().create(_ticket_values)

            return

        _logger.info('Creating COURSE REGISTRATION')

        # first we look for it
        course_student_ids = self.sudo().env['climbing_gym_school.course_student'].search([
            ('course_id', 'in', course_id.ids),
            ('partner_id', '=', partner_id.id)
        ])

        if len(course_student_ids) > 0:
            for cs in course_student_ids:
                cs.sale_order_line = sale_order_line
                cs.pos_order_line = pos_order_line
                cs.partner_id = partner_id
                cs.product_id = product_id
                cs.state = 'accepted'
        else:
            _my_csr = self.sudo().env['climbing_gym_school.course_student'].create({
                'partner_id': partner_id.id,
                'obs': "Created automatically after order confirmation",
                'course_id': course_id.id,
                'product': product_id.id,
                'sale_order_line': sale_order_line.id if sale_order_line is not False else False,
                'pos_order_line': pos_order_line.id if pos_order_line is not False else False,
                'state': 'accepted',
            })

            _logger.info('Created COURSE STUDENT %d' % _my_csr.id)

    @api.model
    def create(self, vals):
        # self.message_post(body='Created package', subject='Package modification', message_type='notification', subtype=None, parent_id=False, attachments=None)
        result = super(CourseStudent, self).create(vals)

        if result:
            result.course_id.update_product_availability()

        return result

    @api.multi
    def write(self, vals):
        result = super(CourseStudent, self).write(vals)

        if result:
            self.course_id.update_product_availability()

        return result