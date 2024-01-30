# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from psycopg2 import sql

from odoo import tools
from odoo import api, fields, models


class FleetReportPetrol(models.Model):
    _name = "fleet.vehicle.petrol.report"
    _description = "Fleet Petrol Analysis Report"
    _auto = False

    
    name = fields.Char('Name', readonly=True)
    date = fields.Date('Date', readonly=True)
    distance = fields.Float('Distance (km)', group_operator="max", readonly=True)
    petrol = fields.Float('Petrol (RM)', group_operator="max", readonly=True)
    vehicle_id = fields.Many2one('fleet.vehicle', 'Vehicle', readonly=True)
    driver_id = fields.Many2one('res.partner', readonly=True)
    petrol_rate = fields.Float('Consumed Petrol Rate (RM/km)', readonly=True)

    def init(self):
        query = """
select  
id,
name,
vehicle_id,
driver_id,
date,
petrol,
greatest(this_month_odometer - last_month_odometer, 0) as distance,
case when (this_month_odometer - last_month_odometer) <= 0 then 0 else petrol / (this_month_odometer - last_month_odometer) end as petrol_rate
from (select p.id, p.name, p.vehicle_id, v.driver_id
			   , p.date, p.petrol
			   , coalesce(o_this_month.value, 0) as this_month_odometer
			   , o_this_month.date as this_month_date
			   , coalesce(o_last_month.value, v.initial_odometer) as last_month_odometer
			   , o_last_month.date as last_month_date
			   , v.license_plate
			   , row_number() over(partition by p.id order by o_this_month.date desc, o_last_month.date desc) r_no
from public.fleet_vehicle_petrol p
left join public.fleet_vehicle_odometer o_this_month 
	on p.vehicle_id = o_this_month.vehicle_id
	and o_this_month.date <= p.date
	and o_this_month.date >= date_trunc('month', p.date)
left join public.fleet_vehicle_odometer o_last_month 
	on p.vehicle_id = o_last_month.vehicle_id
	and o_last_month.date < date_trunc('month', p.date)
	and o_last_month.date >= date_trunc('month', p.date - interval '1' month)
left join public.fleet_vehicle v 
	on p.vehicle_id = v.Id) a
where r_no = 1
"""
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            sql.SQL("""CREATE or REPLACE VIEW {} as ({})""").format(
                sql.Identifier(self._table),
                sql.SQL(query)
            ))