# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
import requests
import logging
import json


class FleetVehiclePetrol(models.Model):
    _name = 'fleet.vehicle.petrol'

    name = fields.Char(compute='_compute_vehicle_log_name', store=True)
    datetime = fields.Datetime('Date & Time', default=fields.Datetime.now)
    odometer = fields.Float('Odometer (km)', group_operator="max")
    petrol = fields.Float('Petrol (RM)', group_operator="max")
    vehicle_id = fields.Many2one('fleet.vehicle', 'Vehicle', required=True)
    driver_id = fields.Many2one(related="vehicle_id.driver_id", string="Driver", readonly=False)
    synced = fields.Integer('Synced')
    synced_display = fields.Char(compute='_get_sync_display', store=False)

    @api.depends('synced')
    def _get_sync_display(self):
        for record in self:
            synced = 'Synced'
            if record.synced == 0:
                synced = 'Not Synced'
            record.synced_display = synced


    @api.depends('vehicle_id', 'datetime')
    def _compute_vehicle_log_name(self):
        for record in self:
            name = record.vehicle_id.name
            if not name:
                name = str(record.datetime)
            elif record.datetime:
                name += ' / ' + str(record.datetime)
            record.name = name

    def quick_sync(self):
        
        self.env['api_controller.api_controller'].quick_sync()
        return True
    
    
    
    def write(self, vals):

        if self.synced == 1:
            vals['synced'] = 0
        res = super(FleetVehiclePetrol, self).write(vals)
        return res