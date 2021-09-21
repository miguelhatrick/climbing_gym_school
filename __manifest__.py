# -*- coding: utf-8 -*-
{
    'name': "climbing_gym_school",
    # climbing_gym_school
    'summary': """
        Climbing gym School management""",

    'description': """
        Climbing gym School management
    """,

    'author': "Miguel Hatrick",
    'website': "http://www.dacosys.com",

    'category': 'Climbing Gym',
    'version': '12.0.2',

    # any module necessary for this one to work correctly
    'depends': ['base',
                'mail',
                'climbing_gym',
                ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',

        'views/career.xml',
        'views/course.xml',
        'views/course_student.xml',
        'views/course_type.xml',
        'views/menu.xml',
        'views/res_partner.xml',

        'views/portal/portal_my_documents.xml',
        'views/portal/portal_course.xml'

    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}
