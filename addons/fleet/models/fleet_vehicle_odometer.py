# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
import requests
import logging
import json


class FleetVehicleOdometer(models.Model):
    _name = 'fleet.vehicle.odometer'
    _description = 'Odometer log for a vehicle'
    _order = 'datetime desc'

    name = fields.Char(compute='_compute_vehicle_log_name', store=True)
    datetime = fields.Datetime('Date & Time', default=fields.Datetime.now)
    odometer_start = fields.Float('Start', group_operator="max")
    odometer_end = fields.Float('End', group_operator="max")
    bucket_amount = fields.Integer('Bucket', required=True)
    loading_weight = fields.Float('Weight (tons)', compute='_compute_loading_weight', readonly=True)
    total = fields.Float('Total', compute='_compute_total', store=True, readonly=True)
    value = fields.Float('Distance', compute='_compute_odometer', store=True, readonly=True)
    vehicle_id = fields.Many2one('fleet.vehicle', 'Vehicle', required=True)
    unit = fields.Selection(related='vehicle_id.odometer_unit', string="Unit", readonly=True)
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

    @api.depends('odometer_start', 'odometer_end')
    def _compute_odometer(self):
        for record in self:
            odometer = record.odometer_end - record.odometer_start
            if odometer < 0:
                odometer = 0
            record.value = odometer

    @api.depends('bucket_amount')
    def _compute_loading_weight(self):
        for record in self:
            weight = 0
            if record.bucket_amount > 0:
                weight = record.bucket_amount / 11
            record.loading_weight = weight
    
    @api.depends('value', 'loading_weight')
    def _compute_total(self):
        for record in self:
            record.total = record.value * record.loading_weight * 0.4

    @api.onchange('vehicle_id')
    def _onchange_vehicle(self):
        if self.vehicle_id:
            self.unit = self.vehicle_id.odometer_unit

    def quick_sync(self):
        
        self.env['api_controller.api_controller'].quick_sync()
        return True
    
    
    def write(self, vals):

        if self.synced == 1:
            vals['synced'] = 0
        res = super(FleetVehicleOdometer, self).write(vals)
        return res