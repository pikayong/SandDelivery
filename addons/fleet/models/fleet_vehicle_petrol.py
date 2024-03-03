# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime
from odoo import api, fields, models
import requests
import logging
import json


class FleetVehiclePetrol(models.Model):
    _name = 'fleet.vehicle.petrol'

    name = fields.Char(compute='_compute_vehicle_log_name', store=True)
    date = fields.Date('Date', default=fields.Date.today)
    # odometer = fields.Float('Odometer (km)', group_operator="max")
    petrol = fields.Float('Petrol (RM)', group_operator="max")
    vehicle_id = fields.Many2one('fleet.vehicle', 'Vehicle', required=True)
    # driver_id = fields.Many2one(related="vehicle_id.driver_id", string="Driver", readonly=False)
    # driver_id = fields.Many2one('res.partner', string="Driver", readonly=False, required=True)
    # driver_id = fields.Many2one('res.partner', compute='_compute_default_driver', store=True, string="Driver", readonly=False, required=True)
    synced = fields.Integer('Synced')
    synced_display = fields.Char('Status', compute='_get_sync_display', store=False)
    # petrol_rate = fields.Float('Consumed Petrol Rate (RM/km)', compute='_get_petrol_rate', store=True, readonly=True)

    # @api.depends('vehicle_id')
    # def _compute_default_driver(self):
    #     for record in self:
    #         if not record.driver_id:
    #             driver_id = record.vehicle_id.driver_id
    #             if driver_id:
    #                 record.driver_id = driver_id

    @api.depends('synced')
    def _get_sync_display(self):
        for record in self:
            synced = 'Synced'
            if record.synced == 0:
                synced = 'Not Synced'
            record.synced_display = synced

    # @api.depends('petrol', 'date', 'vehicle_id')
    # def _get_petrol_rate(self):
    #     _logger = logging.getLogger(__name__)
    #     for record in self:
    #         nextMonthFirstDay = (record.date.replace(day=1) + datetime.timedelta(days=32)).replace(day=1)
    #         _logger.info(type(nextMonthFirstDay))
    #         before_date_odometer = self.env['fleet.vehicle.odometer'].search([('date', '<=', record.date)])
    #         _logger.info(before_date_odometer)
    #         latest_odometer_list = list(filter(lambda x: x.date == max(d.date for d in before_date_odometer), before_date_odometer))
    #         latest_odometer = 0
    #         if len(latest_odometer_list) > 0:
    #             latest_odometer = latest_odometer_list[0].value
    #         _logger.info(latest_odometer)
    #         last_month_odometer = self.env['fleet.vehicle.odometer'].search([('date', '<', record.date.replace(day=1))])
    #         _logger.info(last_month_odometer)
    #         if not last_month_odometer:
    #             _logger.info(record.vehicle_id.initial_odometer)
        # for record in self:
        #     record.petrol_rate = 0
        #     filtered_self = list(filter(lambda x: x.date < record.date and x.vehicle_id == record.vehicle_id, self))
        #     _logger.info(record.date)
        #     _logger.info('filtered_self')
        #     _logger.info(filtered_self)
        #     if (len(filtered_self) > 0):
        #         max_date = max(map(lambda y: y.date, filtered_self))
        #         odometer_diff = record.odometer - list(filter(lambda z: z.date == max_date, filtered_self))[0].odometer
        #         if odometer_diff > 0:
        #             record.petrol_rate = record.petrol / odometer_diff
            


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
        
        return self.env['api_controller.api_controller'].quick_sync()
    
    
    
    def write(self, vals):

        if self.synced == 1:
            vals['synced'] = 0
        res = super(FleetVehiclePetrol, self).write(vals)
        return res