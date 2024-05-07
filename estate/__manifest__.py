{
    'name': 'Estate',
    'license': 'AGPL-3',
    'depends': ['base'],
    "data": [
        'data/estate_property_data.xml',
        'data/estate_property_type_data.xml',
        'data/estate_property_tag_data.xml',

        'security/ir.model.access.csv',

        'views/estate_property_views.xml',
        'views/estate_property_offer_views.xml',
        'views/estate_property_type_views.xml',
        'views/estate_property_tag_views.xml',
        'views/estate_menus.xml',
        'views/res_users_views.xml',
    ]
}