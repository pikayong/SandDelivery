# -*- coding: utf-8 -*-
import json
import logging
import base64

from odoo import http
from odoo.http import request, Response


class ApiController(http.Controller):

    prefix = '__'

    @http.route('/api_controller/api_controller', auth='public')
    def index(self, **kw):
        return "Hello, world"

    # @http.route('/api_controller/api_controller/objects', auth='user', type='json', methods=['POST'], cors='*', csrf=False)
    # def list(self, **data):
    #     _logger = logging.getLogger(__name__)
    #     indexes = http.request.env['api_controller.api_controller'].sudo().updateData(data.get('data'))

    #     # headers = {'Content-Type': 'application/json'}
    #     # vehicles = http.request.env['fleet.vehicle'].search_read([])
    #     # for vehicle in vehicles:
    #     #     for x in vehicle:
    #     #         try:
    #     #             vehicle[x] = str(vehicle[x], "utf-8")
    #     #         finally:
    #     #             continue
    #     # test = { 'results': { 'code': 200, 'message': [{'name': 'test1', 'content': 'whatever'}, {'name': 'test2', 'content': 'whatever'}] } }
    #     # vehiclesResult = { 'results': { 'code': 200, 'data': vehicles } }
    #     # _logger.info(vehiclesResult)
    #     # _logger.info(json.dumps(vehiclesResult, default=str))
        
        
    #     return self.readUnsyncData(indexes)

    @http.route('/api_controller/api_controller/sync_data', auth='user', type='json', methods=['POST'], cors='*', csrf=False)
    def listData(self, **data):
        _logger = logging.getLogger(__name__)

        _logger.info(data)
        # get trips data
        data_trips = data.get('trips')

        if len(data_trips) > 0: 
            for trip in data_trips:
                trip['synced'] = 1
                existingTrip = http.request.env['fleet.vehicle.trip'].search([('name', '=', trip.get('name'))])
                if existingTrip:
                    existingTrip.write(trip)
                else:
                    newTrips = http.request.env['fleet.vehicle.trip'].sudo().create(trip)

        masterDataList = [
            {
                'name': 'res.partner',
                'env': http.request.env['res.partner']
            },
            {
                'name': 'fleet.vehicle.state',
                'env': http.request.env['fleet.vehicle.state']
            },
            {
                'name': 'fleet.vehicle.model.category',
                'env': http.request.env['fleet.vehicle.model.category']
            },
            {
                'name': 'fleet.vehicle.model.brand',
                'env': http.request.env['fleet.vehicle.model.brand']
            },
            {
                'name': 'fleet.vehicle',
                'env': http.request.env['fleet.vehicle']
            },
        ]

        for masterData in masterDataList:
            masterData['data'] = masterData.get('env').search_read([])
            del masterData['env']

        _logger.info(masterDataList)
        
        return self.mapValueToProcessable(masterDataList) 
    
    def mapValueToProcessable(self, masterDataList):
        for masterData in masterDataList:
            for data in masterData.get('data'):
                for x in data:
                    try:
                        data[x] = str(data[x], "utf-8")
                    finally:
                        if type(data[x]) == tuple:
                            if len(data[x]) > 0:
                                data[x] = data[x][0]
                            else:
                                data[x] = None
                        continue
        return masterDataList

    @http.route('/api_controller/api_controller/sync_data_2', auth='user', type='json', methods=['POST'], cors='*', csrf=False)
    def list(self, **data):
        _logger = logging.getLogger(__name__)
        manufacturerId = 0
        modelId = 0
        existingManufacturer = http.request.env['fleet.vehicle.model.brand'].search_read([('name', '=', self.prefix)])
        if len(existingManufacturer) == 0:
            newManufacturer = http.request.env['fleet.vehicle.model.brand'].sudo().create({'name': self.prefix})
            newModel = http.request.env['fleet.vehicle.model'].sudo().create({'name': self.prefix, 'brand_id': newManufacturer.id})
            manufacturerId = newManufacturer.id
            modelId = newModel.id
        else:
            manufacturerId = existingManufacturer[0].get('id')
            existingModel = http.request.env['fleet.vehicle.model'].search_read([('name', '=', self.prefix)])
            if len(existingModel) == 0:
                newModel = http.request.env['fleet.vehicle.model'].sudo().create({'name': self.prefix, 'brand_id': http.request.env['fleet.vehicle.model.brand'].search(['name', '=', self.prefix]).id})
                modelId = newModel.id
            else:
                modelId = existingModel[0].get('id')
        
        data = data.get('data')
        odometers = data.get('odometers')
        petrols = data.get('petrols')
        vehicles = []
        drivers = []

        # Odometers

        for odometer in odometers:
            _logger.info(odometer.get('driver_id'))
            driver_name = odometer.get('driver_id')[1]
            license_plate = odometer.get('license_plate')
            vehicle_id = 0
            driver_id = 0

            existingVehicle = http.request.env['fleet.vehicle'].search_read([('license_plate', '=', license_plate)])
            existingDriver = http.request.env['res.partner'].search_read([('name', '=', driver_name)])
            if len(existingVehicle) == 0 and len(list(filter(lambda x: x == license_plate, vehicles))) == 0:
                vehicles.append(license_plate)
                newVehicle = http.request.env['fleet.vehicle'].sudo().create({'license_plate': license_plate, 'model_id': modelId, 'state_id': 1})
                vehicle_id = newVehicle.id
            else:
                vehicle_id = existingVehicle[0].get('id')
            if len(existingDriver) == 0 and len(list(filter(lambda x: x == driver_name, drivers))) == 0:
                drivers.append(driver_name)
                newDriver = http.request.env['res.partner'].sudo().create({'name': driver_name})
                driver_id = newDriver.id
            else:
                driver_id = existingDriver[0].get('id')
            odometer['vehicle_id'] = vehicle_id
            odometer['driver_id'] = driver_id
            del odometer['license_plate']
            existingOdometer = http.request.env['fleet.vehicle.odometer'].search([('name', '=', odometer.get('name'))])
            if existingOdometer:
                existingOdometer.write(odometer)
            else:
                newDriver = http.request.env['fleet.vehicle.odometer'].sudo().create(odometer)
        

        # Petrols

        for petrol in petrols:
            driver_name = petrol.get('driver_id')[1]
            license_plate = petrol.get('license_plate')
            vehicle_id = 0
            driver_id = 0

            existingVehicle = http.request.env['fleet.vehicle'].search_read([('license_plate', '=', license_plate)])
            existingDriver = http.request.env['res.partner'].search_read([('name', '=', driver_name)])
            if len(existingVehicle) == 0 and len(list(filter(lambda x: x == license_plate, vehicles))) == 0:
                vehicles.append(license_plate)
                newVehicle = http.request.env['fleet.vehicle'].sudo().create({'license_plate': license_plate, 'model_id': modelId, 'state_id': 1})
                vehicle_id = newVehicle.id
            else:
                vehicle_id = existingVehicle[0].get('id')
            if len(existingDriver) == 0 and len(list(filter(lambda x: x == driver_name, drivers))) == 0:
                drivers.append(driver_name)
                newDriver = http.request.env['res.partner'].sudo().create({'name': driver_name})
                driver_id = newDriver.id
            else:
                driver_id = existingDriver[0].get('id')
            petrol['vehicle_id'] = vehicle_id
            petrol['driver_id'] = driver_id
            del petrol['license_plate']
            existingPetrol = http.request.env['fleet.vehicle.petrol'].search([('name', '=', petrol.get('name'))])
            if existingPetrol:
                existingPetrol.write(petrol)
            else:
                newDriver = http.request.env['fleet.vehicle.petrol'].sudo().create(petrol)




        # headers = {'Content-Type': 'application/json'}
        # vehicles = http.request.env['fleet.vehicle'].search_read([])
        # for vehicle in vehicles:
        #     for x in vehicle:
        #         try:
        #             vehicle[x] = str(vehicle[x], "utf-8")
        #         finally:
        #             continue
        # test = { 'results': { 'code': 200, 'message': [{'name': 'test1', 'content': 'whatever'}, {'name': 'test2', 'content': 'whatever'}] } }
        # vehiclesResult = { 'results': { 'code': 200, 'data': vehicles } }
        # _logger.info(vehiclesResult)
        # _logger.info(json.dumps(vehiclesResult, default=str))
        
        return []
        return self.readUnsyncData(indexes)
    
    def readUnsyncData(self, indexes):
        _logger = logging.getLogger(__name__)
        # indexes = [
        #     {
        #         'name': 'manufacturers',
        #         'data': http.request.env['fleet.vehicle.model.brand'].search_read([('synced', '!=', 1)])
        #     },
        #     {
        #         'name': 'categories',
        #         'data': http.request.env['fleet.vehicle.model.category'].search_read([('synced', '!=', 1)])
        #     },
        #     {
        #         'name': 'models',
        #         'data': http.request.env['fleet.vehicle.model'].search_read([('synced', '!=', 1)])
        #     },
        #     {
        #         'name': 'vehicles',
        #         'data': http.request.env['fleet.vehicle'].search_read([('synced', '!=', 1)])
        #     },
        # ]
        for index in indexes:
            for vehicle in index.get('data'):
                for x in vehicle:
                    try:
                        vehicle[x] = str(vehicle[x], "utf-8")
                    finally:
                        if type(vehicle[x]) == tuple:
                            if len(vehicle[x]) > 0:
                                vehicle[x] = vehicle[x][0]
                            else:
                                vehicle[x] = None
                        continue
        
        result = {
            'manufacturers': list(filter(lambda x: x.get('json_name') == 'manufacturers', indexes))[0].get('data'),
            'categories': list(filter(lambda x: x.get('json_name') == 'categories', indexes))[0].get('data'),
            'models': list(filter(lambda x: x.get('json_name') == 'models', indexes))[0].get('data'),
            'vehicles': list(filter(lambda x: x.get('json_name') == 'vehicles', indexes))[0].get('data'),
        }
        
        testServerSideResult = {
            'manufacturers': [],
            'categories': [],
            'models': [],
            'vehicles': [],
        }
        _logger.info(result)
        return result
    
    