# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
import requests
import logging
import json


class FleetVehicleTrip(models.Model):
    _name = 'fleet.vehicle.trip'
    _description = 'Trip Transactions Log'
    _order = 'datetime desc'

    name = fields.Char(compute='_compute_vehicle_log_name', store=True)
    ref_no = fields.Char('Reference No', store=True)
    datetime = fields.Datetime('Date & Time', default=fields.Datetime.now)
    trip_id = fields.Many2one('fleet.vehicle.trip.master', 'Trip', required=True)
    distance = fields.Integer('Distance (km)', compute='_compute_trip_distance', store=True, required=True, readonly=False)
    price = fields.Float('Unit Price (MYR)', compute='_compute_trip_price', store=True, required=True, readonly=False)
    bucket = fields.Integer('Ton/bucket', compute='_compute_trip_bucket', store=True, required=True, readonly=False)
    bucket_amount = fields.Integer('Bucket', store=True)
    loading_weight = fields.Float('Weight (tons)', compute='_compute_loading_weight', store=True, readonly=False)
    total = fields.Float('Total (RM)', compute='_compute_total', store=True, readonly=True)
    vehicle_id = fields.Many2one('fleet.vehicle', 'Vehicle', required=True)
    unit = fields.Selection(related='vehicle_id.odometer_unit', string="Unit", readonly=True)
    # driver_id = fields.Many2one(related="vehicle_id.driver_id", string="Driver", readonly=False)
    driver_id = fields.Many2one('res.partner', compute='_compute_default_driver', store=True, string="Driver", readonly=False, required=True)
    # driver_id = fields.Many2one('res.partner', string="Driver", readonly=False, required=True)
    synced = fields.Integer('Synced')
    synced_display = fields.Char('Status', compute='_get_sync_display', store=False)

    @api.depends('vehicle_id')
    def _compute_default_driver(self):
        for record in self:
            if not record.driver_id:
                driver_id = record.vehicle_id.driver_id
                if driver_id:
                    record.driver_id = driver_id

    @api.depends('trip_id')
    def _compute_trip_distance(self):
        for record in self:
            distance = record.trip_id.distance
            if not distance:
                distance = 0
            record.distance = distance

    @api.depends('trip_id')
    def _compute_trip_price(self):
        for record in self:
            price = record.trip_id.price
            if not price:
                price = 0
            record.price = price

    @api.depends('trip_id')
    def _compute_trip_bucket(self):
        for record in self:
            bucket = record.trip_id.bucket
            if not bucket:
                bucket = 0
            record.bucket = bucket

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

    @api.depends('trip_id', 'bucket_amount', 'bucket')
    def _compute_loading_weight(self):
        for record in self:
            weight = record.trip_id.weight
            if record.bucket > 0 and record.bucket_amount > 0:
                weight = record.bucket_amount * record.bucket
            record.loading_weight = weight
    
    @api.depends('distance', 'loading_weight', 'price')
    def _compute_total(self):
        for record in self:
            record.total = record.distance * record.loading_weight * record.price

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
        res = super(FleetVehicleTrip, self).write(vals)
        return res