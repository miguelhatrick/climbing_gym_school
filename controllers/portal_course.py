# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import datetime
import json
import pdb

from odoo.addons.website_form.controllers.main import WebsiteForm
from odoo import fields, http, _
from odoo.addons.base.models.ir_qweb_fields import nl2br
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.http import request
from odoo.addons.portal.controllers.mail import _message_post_helper
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
from odoo.osv import expression


class CustomerPortalSchool(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(CustomerPortalSchool, self)._prepare_portal_layout_values()
        _partner = request.env.user.partner_id

        course = request.env['climbing_gym_school.course']
        course_count = course.search_count([
            ('state', 'in', ['active']),
            # ('state', 'in', ['sale', 'done'])
        ])

        values.update({
            'course_count': course_count,
        })
        return values

    @http.route(['/my/courses', '/my/courses/page/<int:page>'], type='http', auth="user",
                website=True)
    def portal_my_courses(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        _course = request.env['climbing_gym_school.course']

        domain = [
            ('state', 'in', ['active', 'closed'])
        ]

        searchbar_sortings = {
            'date': {'label': _('Creation date'), 'order': 'create_date desc'},
            'stage': {'label': _('Stage'), 'order': 'state'},
        }

        # default sortby order
        if not sortby:
            sortby = 'date'
        sort_order = searchbar_sortings[sortby]['order']

        archive_groups = self._get_archive_groups('climbing_gym_school.course', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        quotation_count = _course.search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/courses",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=quotation_count,
            page=page,
            step=self._items_per_page
        )
        # search the count to display, according to the pager data
        courses = _course.search(domain, order=sort_order, limit=self._items_per_page,
                                 offset=pager['offset'])

        request.session['my_courses_history'] = courses.ids[:100]

        values.update({
            'date': date_begin,
            'courses': courses.sudo(),
            'partner': partner,
            'page_name': 'Courses',
            'pager': pager,
            'archive_groups': archive_groups,
            'default_url': '/my/courses',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("climbing_gym_school.portal_my_courses", values)

    @http.route(['/my/courses/register'], type='http', auth="user", website=True)
    def portal_my_medical_certificate_form(self, **kwargs):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        _course = request.env['climbing_gym_school.course']
        _course_student = request.env['climbing_gym_school.course_student']

        course = _course.search([('id', '=', kwargs['course_id'])])
        # ,('res_id', '=', _mc.id)]

        # If not registered register

        _mc = _course_student.sudo().create({
            'student_id': partner.id,
            'course_id': course.id,
            'state': 'pending'
            })

        return self.portal_my_courses()


class CustomerPortalForm(WebsiteForm):
    @http.route('/website_form/shop.climbing_gym.medical_certificate', type='http', auth="public", methods=['POST'],
                website=True)
    def website_form_medical_certificate(self, **kwargs):
        partner = request.env.user.partner_id
        model_record = request.env.ref('climbing_gym.model_climbing_gym_medical_certificate')

        # date
        issue_date = datetime.datetime.strptime(kwargs['issue_date'], "%Y-%m-%d").date()
        kwargs['issue_date'] = issue_date.strftime("%d/%m/%Y")

        try:
            data = self.extract_data(model_record, kwargs)
        except ValidationError as e:
            return json.dumps({'error_fields': e.args[0]})

        _medicalCertificate = request.env['climbing_gym.medical_certificate']

        _mc = _medicalCertificate.sudo().create({
            'partner_id': partner.id,
            'issue_date': issue_date,
            'doctor_name': kwargs['doctor_name'],
            'doctor_license': kwargs['doctor_license']
        }
        )

        if data['custom']:
            values = {
                'body': nl2br(data['custom']),
                'model': 'climbing_gym.medical_certificate',
                'message_type': 'comment',
                'no_auto_thread': False,
                'res_id': _mc.id,
            }
            request.env['mail.message'].sudo().create(values)

        if data['attachments']:
            _id = self.insert_attachment(model_record, _mc.id, data['attachments'])

        _at_ids = request.env['ir.attachment'].sudo().search([('res_model', '=', 'climbing_gym.medical_certificate'),
                                                              ('res_id', '=', _mc.id)])

        for _id in _at_ids:
            _mc.attachment_ids = [(4, _id.id)]

        return json.dumps({'id': _mc.id})
