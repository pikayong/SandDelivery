# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class FleetVehicleState(models.Model):
    _name = 'fleet.vehicle.state'
    _order = 'sequence asc'
    _description = 'Vehicle Status'

    ex_id = fields.Integer(store=True)
    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer()
    visibility = fields.Selection([('1', 'Visible'), ('0', 'Hidden')], string='Visible on Selection')

    _sql_constraints = [('fleet_state_name_unique', 'unique(name)', 'State name already exists')]



    def create(self, vals):
        result = super().create(vals)
        if result.ex_id == 0: 
            result.sudo().write({'ex_id': result.id})
        return result