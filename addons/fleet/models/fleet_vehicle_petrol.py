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
    petrol_rate = fields.Float('Petrol Rate', compute='_get_petrol_rate', store=False)

    @api.depends('synced')
    def _get_sync_display(self):
        for record in self:
            synced = 'Synced'
            if record.synced == 0:
                synced = 'Not Synced'
            record.synced_display = synced

    @api.depends('petrol', 'odometer', 'datetime', 'vehicle_id')
    def _get_petrol_rate(self):
        _logger = logging.getLogger(__name__)
        for record in self:
            record.petrol_rate = 0
            filtered_self = list(filter(lambda x: x.datetime < record.datetime and x.vehicle_id == record.vehicle_id, self))
            _logger.info(record.datetime)
            _logger.info('filtered_self')
            _logger.info(filtered_self)
            if (len(filtered_self) > 0):
                max_date = max(map(lambda y: y.datetime, filtered_self))
                odometer_diff = record.odometer - list(filter(lambda z: z.datetime == max_date, filtered_self))[0].odometer
                if odometer_diff > 0:
                    record.petrol_rate = record.petrol / odometer_diff
            


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