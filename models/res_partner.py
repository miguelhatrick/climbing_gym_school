# Copyright (C)
# Copyright 2020- (<http://www.a>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import pdb
from datetime import datetime

from odoo import fields, models, api


class ResPartnerClimbingSchool(models.Model):
    """Climbing school addons to partner."""
    _inherit = "res.partner"

    climbing_gym_school_course_student = fields.One2many(
        'climbing_gym_school.course_student', inverse_name='partner_id', string='Course student registration',
        readonly=False, track_visibility=False)

