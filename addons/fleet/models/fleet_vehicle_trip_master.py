# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
import requests
import logging
import json


class FleetVehicleTripMaster(models.Model):
    _name = 'fleet.vehicle.trip.master'
    _description = 'Trip Reference for each trip'

    name = fields.Char('Trip Name', required=True)
    distance = fields.Integer('Distance (km)', required=True)
    price = fields.Float('Unit Price(MYR)', required=True)
    bucket = fields.Integer('Buckets per 1ton', required=True)
    weight = fields.Integer('Default Weight (ton)', required=True)