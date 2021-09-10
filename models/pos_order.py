from datetime import datetime
import pdb
import logging
from odoo import fields, models, api

_logger = logging.getLogger(__name__)


class PosOrderSchool(models.Model):
    _inherit = 'pos.order'

    @api.multi
    def action_pos_order_paid(self):
        # pdb.set_trace()
        self.create_course_registration()
        return super(PosOrderSchool, self).action_pos_order_paid()

    @api.multi
    def create_course_registration(self):
        """Creates a new Registration to courses based on the products"""

        active_course_ids = self.sudo().env['climbing_gym_school.course'].search([
            ('state', 'in', ['active'])
        ])
        _logger.info('Begin COURSE REGISTRATION from POS SALE... ')

        for order in self:
            for line in order.lines:

                course_ids = list(filter(lambda x: line.product_id in x.product_product_ids, active_course_ids))
                if len(course_ids) > 0:
                    self.sudo().env['climbing_gym_school.course_student'].create_or_confirm_course_registration(self,
                                                                                                                line,
                                                                                                                course_ids[
                                                                                                                    0])
