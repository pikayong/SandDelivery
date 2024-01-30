# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from psycopg2 import sql

from odoo import tools
from odoo import api, fields, models


class FleetReportOdometer(models.Model):
    _name = "fleet.vehicle.odometer.report"
    _description = "Fleet Odometer Analysis Report"
    _auto = False

    
    name = fields.Char('Name', readonly=True)
    date = fields.Date('Date', readonly=True)
    value = fields.Float('Odometer (km)', group_operator="max", readonly=True)
    distance = fields.Float('Distance (km)', group_operator="sum", readonly=True)
    vehicle_id = fields.Many2one('fleet.vehicle', 'Vehicle', readonly=True)
    driver_id = fields.Many2one('res.partner', 'Driver', readonly=True)

    def init(self):
        query = """
select 
	id,
	name,
	date,
	value,
	case when previous_value is null then value - initial_odometer else value - previous_value end as distance,
	vehicle_id,
	driver_id
from
(
select
	o.id,
	o.name,
	o.date,
	o.value,
	LAG(o.value) OVER (PARTITION BY o.vehicle_id ORDER BY o.date) AS previous_value,
	o.vehicle_id,
	o.driver_id,
	v.initial_odometer
from
	public.fleet_vehicle_odometer o
left join 
	public.fleet_vehicle v
	on o.vehicle_id = v.id
)
order by
	date desc
"""
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            sql.SQL("""CREATE or REPLACE VIEW {} as ({})""").format(
                sql.Identifier(self._table),
                sql.SQL(query)
            ))