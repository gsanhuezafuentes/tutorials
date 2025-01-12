from odoo import fields, models

class Users(models.Model):
    _inherit = "res.users"

    property_ids = fields.One2many("estate.property", "salesperson_id", domain=[("status", "in", ["new", "offer_received"])])
