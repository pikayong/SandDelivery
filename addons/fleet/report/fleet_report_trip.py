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
    date = fields.Date('Date', readonly=True)
    vehicle_id = fields.Many2one('fleet.vehicle', 'Vehicle', readonly=True)
    driver_id = fields.Many2one('res.partner', 'Driver', readonly=True)
    trip_id = fields.Many2one('fleet.vehicle.trip.master', 'Trip', readonly=True)
    loading_weight = fields.Float('Weight (tons)', group_operator="sum", readonly=True)
    distance = fields.Float('Distance (km)', group_operator="sum", readonly=True)
    total = fields.Float('Total (RM)', group_operator="sum", readonly=True)
    license_plate = fields.Char('Vehicle', readonly=True)

    def init(self):
        query = """
select
	t.id,
	t.name,
	t.datetime,
    DATE(t.datetime) as date,
	t.vehicle_id,
	t.driver_id,
	t.trip_id,
	t.loading_weight,
	t.distance,
	t.total,
    v.license_plate
from
	public.fleet_vehicle_trip t
inner join
    public.fleet_vehicle v on t.vehicle_id = v.id
"""
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            sql.SQL("""CREATE or REPLACE VIEW {} as ({})""").format(
                sql.Identifier(self._table),
                sql.SQL(query)
            ))