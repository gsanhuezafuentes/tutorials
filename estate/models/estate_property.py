from datetime import timedelta

from odoo import api, models, fields
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero

class EstateProperty(models.Model):
    _name = 'estate.property'
    _description = 'Estate Property'

    name = fields.Char(default="Unknown")
    description = fields.Text()
    postcode = fields.Char()
    date_availability = fields.Date(default=lambda args: fields.Date.today() + timedelta(days=30*3))
    expected_price = fields.Float()
    selling_price = fields.Float(readonly=True)
    bedrooms = fields.Integer(default=2)
    living_area = fields.Integer()
    facades = fields.Integer()
    garage = fields.Boolean()
    garden = fields.Boolean()
    garden_area = fields.Integer()
    garden_orientation = fields.Selection(
        selection=[
            ('north', 'North'),
            ('south', 'South'),
            ('east', 'East'),
            ('west', 'West'),
        ]
    )
    last_seen = fields.Datetime("Last Seen", default=fields.Datetime.now)
    active = fields.Boolean(default=True)
    status = fields.Selection(
        selection=[
            ('new', 'New'),
            ('offer_received', 'Offer Received'),
            ('offer_accepted', 'Offer Accepted'),
            ('sold', 'Sold'),
            ('canceled', 'Canceled'),
        ]
    )
    property_type_id = fields.Many2one('estate.property.type')
    buyer_id = fields.Many2one('res.partner')
    salesperson_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    tags_ids = fields.Many2many('estate.property.tag')
    offers_ids = fields.One2many('estate.property.offer', 'property_id')
    total_area = fields.Float(compute="_compute_total_area")
    best_price = fields.Float(compute="_compute_best_price")

    _sql_constraints = [
        ("check_expected_price", "CHECK(expected_price > 0)", "The expected price must be strictly positive"),
        ("check_selling_price", "CHECK(selling_price >= 0)", "The selling price must be positive"),
    ]

    @api.depends('living_area', 'garden_area')
    def _compute_total_area(self):
        for record in self:
            record.total_area = record.living_area + record.garden_area

    
    @api.depends('offers_ids.price')
    def _compute_best_price(self):
        for record in self:
            record.best_price = max(record.offers_ids.mapped('price'), default=0)

    @api.onchange('garden')
    def _onchange_garden(self):
        if self.garden:
            self.garden_area = 10
            self.garden_orientation = 'north'
        else:
            self.garden_area = 0
            self.garden_orientation = ''
    
    def action_sold(self):
        for record in self:
            if record.status == 'canceled':
                raise UserError("Can't mark as sold a canceled property")
            record.status = 'sold'
        return True
    
    def action_cancel(self):
        for record in self:
            if record.status == 'sold':
                raise UserError("Can't cancel a sold property")
            record.status = 'canceled'
        return True
    
    @api.constrains('selling_price', 'expected_price')
    def _check_selling_price(self):
        for record in self:
            if (
                not float_is_zero(record.selling_price, 2) 
                and float_compare(record.selling_price, record.expected_price * .9) < 0
            ):
                raise ValidationError("The selling price can't be lower than 90% of the expected price")
      
class EstatePropertyType(models.Model):
    _name = 'estate.property.type'
    _description = 'Estate Property Type'

    name = fields.Char(required=True)


class EstatePropertyTag(models.Model):
    _name = 'estate.property.tag'
    _description = 'Estate Property Tag'

    name = fields.Char(required=True, unique=True)

    _sql_constraints = [
        ("unique_name", "UNIQUE(name)", "The name must be unique"),
    ]


class EstatePropertyOffer(models.Model):
    _name = 'estate.property.offer'
    _description = 'Estate Property Offer'

    price = fields.Float()
    status = fields.Selection(
        selection=[
            ('accepted', 'Accepted'),
            ('refused', 'Refused'),
        ]
    )
    valid_from = fields.Date()
    valid_to = fields.Date()
    validity = fields.Integer(default=7)
    date_deadline = fields.Date(compute="_compute_date_deadline", inverse="_inverse_date_deadline")
    partner_id = fields.Many2one('res.partner')
    property_id = fields.Many2one('estate.property')

    _sql_constraints = [
        ("check_price", "CHECK(price > 0)", "The price must be strictly positive"),
    ]

    @api.depends('create_date', 'validity')
    def _compute_date_deadline(self):
        for record in self:
            created_date = record.create_date or fields.Date.today()
            record.date_deadline =  created_date + timedelta(days=record.validity)
    
    def _inverse_date_deadline(self):
        for record in self:
            record.validity = (record.date_deadline - record.create_date.date()).days
    
    def accept_offer(self):
        for record in self:
            record.property_id.selling_price = record.price
            record.property_id.buyer_id = record.partner_id
            record.status = 'accepted'
        return True

    def refuse_offer(self):
        for record in self:
            record.status = 'refused'

        return True
