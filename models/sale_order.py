from datetime import datetime
import pdb
import logging
from odoo import fields, models, api

_logger = logging.getLogger(__name__)


class SaleOrderSchool(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_confirm(self):
        # pdb.set_trace()

        val = super(SaleOrderSchool, self).action_confirm()

        self.create_course_registration()

        return val

    @api.multi
    def create_course_registration(self):
        """Creates a new Registration to courses based on the products"""

        active_course_ids = self.sudo().env['climbing_gym_school.course'].search([
            ('state', 'in', ['active', 'closed'])
        ])
        _logger.info('Begin COURSE REGISTRATION from WEB SALE... ')

        for order in self:
            for line in order.order_line:

                course_ids = list(filter(lambda x: line.product_id in x.product_product_ids, active_course_ids))
                if len(course_ids) > 0:
                    if course_ids[0].state == 'active':
                        self.sudo().env['climbing_gym_school.course_student'].create_or_confirm_course_registration(
                            self,
                            line,
                            course_ids[0])

                        if line.product_uom_qty > 1:
                            _ticket_values = {
                                'company_id': None,
                                'category_id': self.env['helpdesk.ticket.category'].sudo().search(
                                    [('name', '=', 'Membresías / Cuotas')]).id,

                                'partner_name': order.partner_id.name,
                                'partner_email': order.partner_id.email,

                                'description': "More than 1 course paid - %s - %s" % (
                                order.id, course_ids[0].description),
                                'name': '>1 courses paid!',
                                'attachment_ids': False,
                                'channel_id': self.env['helpdesk.ticket.channel'].sudo().search(
                                    [('name', '=', 'Web')]).id,
                                'partner_id': order.partner_id.id,
                                'team_id': self.env['helpdesk.ticket.team'].sudo().search(
                                    [('name', '=', 'Secretaria')]).id,
                            }
                            new_ticket = self.env['helpdesk.ticket'].sudo().create(_ticket_values)

                    else:
                        # TODO: Verify this
                        # create Ticket
                        _ticket_values = {
                            'company_id': None,
                            'category_id': self.env['helpdesk.ticket.category'].sudo().search(
                                [('name', '=', 'Membresías / Cuotas')]).id,

                            'partner_name': order.partner_id.name,
                            'partner_email': order.partner_id.email,

                            'description': "No active course for purchase - %s" % order.id,
                            'name': 'No active course!',
                            'attachment_ids': False,
                            'channel_id': self.env['helpdesk.ticket.channel'].sudo().search([('name', '=', 'Web')]).id,
                            'partner_id': order.partner_id.id,
                            'team_id': self.env['helpdesk.ticket.team'].sudo().search([('name', '=', 'Secretaria')]).id,
                        }
                        new_ticket = self.env['helpdesk.ticket'].sudo().create(_ticket_values)
