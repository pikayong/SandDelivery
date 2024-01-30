# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from psycopg2 import sql

from odoo import tools
from odoo import api, fields, models


class FleetReportTrip(models.Model):
    _name = "fleet.vehicle.trip.report"
    _description = "Trip Analysis Report"
    _auto = False

    
    name = fields.Char('Name', readonly=True)
    datetime = fields.Datetime('Date & Time', readonly=True)
    vehicle_id = fields.Many2one('fleet.vehicle', 'Vehicle', readonly=True)
    driver_id = fields.Many2one('res.partner', 'Driver', readonly=True)
    trip_id = fields.Many2one('fleet.vehicle.trip.master', 'Trip', readonly=True)
    loading_weight = fields.Float('Weight (tons)', group_operator="max", readonly=True)
    distance = fields.Float('Distance (km)', group_operator="sum", readonly=True)
    total = fields.Float('Total (RM)', group_operator="sum", readonly=True)

    def init(self):
        query = """
select
	id,
	name,
	datetime,
	vehicle_id,
	driver_id,
	trip_id,
	loading_weight,
	distance,
	total
from
	public.fleet_vehicle_trip
"""
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            sql.SQL("""CREATE or REPLACE VIEW {} as ({})""").format(
                sql.Identifier(self._table),
                sql.SQL(query)
            ))