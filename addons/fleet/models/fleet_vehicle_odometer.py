# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
import requests
import logging
import json


class FleetVehicleOdometer(models.Model):
    _name = 'fleet.vehicle.odometer'
    _description = 'Odometer log for a vehicle'
    _order = 'date desc'

    name = fields.Char(compute='_compute_vehicle_log_name', store=True)
    date = fields.Date('Date', default=fields.Date.today)
    value = fields.Float('Odometer (km)', group_operator="max")
    vehicle_id = fields.Many2one('fleet.vehicle', 'Vehicle', required=True)
    # driver_id = fields.Many2one(related="vehicle_id.driver_id", string="Driver", readonly=False)
    driver_id = fields.Many2one('res.partner', compute='_compute_default_driver', store=True, string="Driver", readonly=False, required=True)
    synced = fields.Integer('Synced')
    synced_display = fields.Char('Status', compute='_get_sync_display', store=False)

    @api.depends('vehicle_id')
    def _compute_default_driver(self):
        for record in self:
            if not record.driver_id:
                driver_id = record.vehicle_id.driver_id
                if driver_id:
                    record.driver_id = driver_id

    @api.depends('synced')
    def _get_sync_display(self):
        for record in self:
            synced = 'Synced'
            if record.synced == 0:
                synced = 'Not Synced'
            record.synced_display = synced

    @api.depends('vehicle_id', 'date')
    def _compute_vehicle_log_name(self):
        for record in self:
            name = record.vehicle_id.name
            if not name:
                name = str(record.date)
            elif record.date:
                name += ' / ' + str(record.date)
            record.name = name

    def quick_sync(self):
        
        self.env['api_controller.api_controller'].quick_sync()
        return True
    
    
    def write(self, vals):

        if self.synced == 1:
            vals['synced'] = 0
        res = super(FleetVehicleOdometer, self).write(vals)
        return res