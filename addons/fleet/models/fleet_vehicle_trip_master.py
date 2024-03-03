# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
import requests
import logging
import json


class FleetVehicleTripMaster(models.Model):
    _name = 'fleet.vehicle.trip.master'
    _description = 'Trip Reference for each trip'

    ex_id = fields.Integer(store=True)
    name = fields.Char('Trip Name', required=True)
    distance = fields.Integer('Distance (km)', required=True)
    price = fields.Float('Unit Price(MYR)', required=True)
    bucket = fields.Integer('Ton/bucket', required=True)
    weight = fields.Integer('Default Weight (ton)', required=True)


    def create(self, vals):
        result = super().create(vals)
        if result.ex_id == 0: 
            result.sudo().write({'ex_id': result.id})
        return result