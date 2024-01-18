# -*- coding: utf-8 -*-

from odoo import http
from odoo import models, fields, api
import logging
import json
import requests


class api_controller(models.Model):
    _name = 'api_controller.api_controller'
    _description = 'api_controller.api_controller'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
    
    def quick_sync(self):
        _logger = logging.getLogger(__name__)

        parameter = {
            "db": "sanddelivery",
            "login": "admin",
            "password": "123asdASD!@#",    
        }

        data = self.getData()
        
        _logger.info(data)

        headers = {'Content-type': 'application/json'}      
        AUTH_URL = "http://localhost:8069/web/session/authenticate/"
        data = {
                "jsonrpc": "2.0",
                "params": {
                        "login": parameter['login'],
                        "password": parameter['password'],
                        "db": parameter['db'],
                        "data": data
                    }
                }  
        res = requests.post(AUTH_URL, data=json.dumps(data, default=str),headers=headers)
        session_id = res.cookies["session_id"]
        base_url = "localhost:8069/api_controller/api_controller/sync_data" # your api 
        json_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            }
        cookies = {
            'login': "admin", 
            'password': '123asdASD!@#',
            'session_id':session_id
            }
        response = requests.post("http://{}".format(base_url), data = json.dumps(data, default=str), headers=json_headers, cookies=cookies)
        _logger.info(response.status_code)
        _logger.info(response.json())
        self.Synced()
        # self.updateData(response.json().get('result'), True)
        return True
    
    def getData(self):
        _logger = logging.getLogger(__name__)
        indexes = self.getIndexes_getList()
        for index in indexes:
            index['data'] = self.searchReadDataProcessing(index.get('data'))
            # for vehicle in index.get('data'):
            #     for x in vehicle:
            #         try:
            #             vehicle[x] = str(vehicle[x], "utf-8")
            #         finally:
            #             if type(vehicle[x]) == tuple:
            #                 if len(vehicle[x]) > 0:
            #                     vehicle[x] = vehicle[x][0]
            #                 else:
            #                     vehicle[x] = None
            #             if x == 'license_plate':
            #                  vehicle[x] = vehicle[x] + '8'
            #             continue
        result = {
            # 'manufacturers': list(filter(lambda x: x.get('name') == 'manufacturers', indexes))[0].get('data'),
            # 'categories': list(filter(lambda x: x.get('name') == 'categories', indexes))[0].get('data'),
            # 'models': list(filter(lambda x: x.get('name') == 'models', indexes))[0].get('data'),
            # 'vehicles': list(filter(lambda x: x.get('name') == 'vehicles', indexes))[0].get('data'),
            'odometers': list(filter(lambda x: x.get('name') == 'odometers', indexes))[0].get('data'),
            'petrols': list(filter(lambda x: x.get('name') == 'petrols', indexes))[0].get('data'),
        }
        
        testServerSideResult = {
            'manufacturers': [],
            'categories': [],
            'models': [],
            'vehicles': [],
        }
        _logger.info(result)
        return result
    
    def searchReadDataProcessing(self, data):
        for vehicle in data:
            for x in vehicle:
                try:
                    vehicle[x] = str(vehicle[x], "utf-8")
                finally:
                    if type(vehicle[x]) == tuple:
                        if len(vehicle[x]) > 1:
                            vehicle[x] = list(vehicle[x])
                        elif len(vehicle[x]) == 1:
                            vehicle[x] = vehicle[x][0]
                        else:
                            vehicle[x] = None
                    continue
            vehicle['license_plate'] = http.request.env['fleet.vehicle'].search([('id', '=', vehicle['vehicle_id'][0])]).license_plate
            vehicle['driver_id'][1] = 'Nobody'
        return data
    
    def Synced(self):
        unsyncedData = http.request.env['fleet.vehicle.odometer'].search([('synced', '=', 0)])
        for record in unsyncedData:
            record.write({'synced': 1})

    def updateData_V2(self, data, isLocal = False):
        _logger = logging.getLogger(__name__)

        # indexes = self.getIndexes_withReqEnv(data)
        
        tobeUpdatedOdometers = data.get('odometers')

        # Create Manufacturer and Model if not existed
        newManufacturer = http.request.env['fleet.vehicle.model.brand'].search_read([('name', '=', 'New Manufacture')])
        newModel = http.request.env['fleet.vehicle.model'].search_read([('name', '=', 'New Model')])


        vehicles = []
        for odometer in tobeUpdatedOdometers:
            # Check Vehicle Existance
            if odometer.get('vehicle_id') != None:
                if len(list(http.request.env['fleet.vehicle'].search_read([('name', '=', odometer.get('vehicle_id'))]))) == 0:
                    http.request.env['fleet.vehicle'].sudo().create()
        


    def updateData(self, data, isLocal = False):
        _logger = logging.getLogger(__name__)

        indexes = self.getIndexes_withReqEnv(data)

        if isLocal:
            for index_obj in indexes:
                _logger.info(index_obj)
                vehicles_raw = index_obj.get('data') + self.searchReadDataProcessing(index_obj.get('request_env').search_read([('synced', '!=', 1)]))
                if vehicles_raw != None and len(vehicles_raw) > 0:
                    vehicles = list(map(lambda x: self.getVehicle(x, index_obj.get('json_name')), vehicles_raw))
                    bUpdateCreatedVehicles = self.to_be_created_with_id(vehicles)
                    bUpdateCreatedVehiclesIds = list(map(lambda x: x.get('id'), bUpdateCreatedVehicles))
                    existingVehicles = index_obj.get('request_env').search([('id', 'in', bUpdateCreatedVehiclesIds)])
                    _logger.info(index_obj)
                    for existingVehicle in existingVehicles:
                        vehicle = list(filter(lambda x: x.get('id') == existingVehicle.id, bUpdateCreatedVehicles))
                        if (len(vehicle) > 0):
                            existingVehicle.write(self.removed_id(vehicle[0]))
                    createdVehicle = index_obj.get('request_env').sudo().create(self.to_be_created(filter(lambda x: x.get('id') not in bUpdateCreatedVehiclesIds, vehicles)))
                    bUpdatedVehicles = self.to_be_updated(vehicles)
                    bUpdatedVehiclesIds = list(map(lambda x: x.get('id'), bUpdatedVehicles))
                    updatedVehicles = index_obj.get('request_env').search([('id', 'in', bUpdatedVehiclesIds)])
                    _logger.info(index_obj)
                    for updatedVehicle in updatedVehicles:
                        vehicle = list(filter(lambda x: x.get('id') == updatedVehicle.id, bUpdatedVehicles))
                        if (len(vehicle) > 0):
                            updatedVehicle.write(vehicle[0])


                    localCreateVehicles_raw = list(map(lambda record: self.updateAllUpdatedSynced(record), index_obj.get('request_env').search_read(['|', ('id', 'in', createdVehicle.ids), ('synced', '=', 0)])))
                    localUpdateVehicles_raw = list(index_obj.get('request_env').search_read([('synced', '=', 2)]))
                    _logger.info('Created Vehicles')
                    localVehiclesData = localCreateVehicles_raw + localUpdateVehicles_raw
                    index_obj['data'] = list(map(lambda x: self.getVehicle(x, index_obj.get('json_name')), localVehiclesData))
            return indexes

        for index_obj in indexes:
            _logger.info(index_obj)
            vehicles_raw = index_obj.get('data')
            if vehicles_raw != None and len(vehicles_raw) > 0:
                vehicles = list(map(lambda x: self.getVehicle(x, index_obj.get('json_name')), vehicles_raw))
                bUpdatedVehicles = self.to_be_updated(vehicles)
                bUpdatedVehiclesIds = list(map(lambda x: x.get('id'), bUpdatedVehicles))
                createdVehicle = index_obj.get('request_env').sudo().create(self.to_be_created(vehicles))
                updatedVehicles = index_obj.get('request_env').search([('id', 'in', bUpdatedVehiclesIds)])
                _logger.info(index_obj)
                for updatedVehicle in updatedVehicles:
                    vehicle = list(filter(lambda x: x.get('id') == updatedVehicle.id, bUpdatedVehicles))
                    if (len(vehicle) > 0):
                        updatedVehicle.write(vehicle[0])


                localCreateVehicles_raw = list(map(lambda record: self.updateAllUpdatedSynced(record), index_obj.get('request_env').search_read(['|', ('id', 'in', createdVehicle.ids), ('synced', '=', 0)])))
                localUpdateVehicles_raw = list(index_obj.get('request_env').search_read([('synced', '=', 2)]))
                _logger.info('Created Vehicles')
                localVehiclesData = localCreateVehicles_raw + localUpdateVehicles_raw
                index_obj['data'] = list(map(lambda x: self.getVehicle(x, index_obj.get('json_name')), localVehiclesData))
        return indexes
    
    def updateAllUpdatedSynced(self, data):
        data['synced'] = 0
        return data
    
    def to_be_created(self, records):
        _logger = logging.getLogger(__name__)
        results = list(map(lambda x: self.removed_id(self.update_to_synced(x)), filter(lambda data: data.get('synced') == 0, records)))
        _logger.info('--v--Creation--v--')
        _logger.info(results)
        return results
    
    def to_be_created_with_id(self, records):
        _logger = logging.getLogger(__name__)
        results = list(map(lambda x: self.update_to_synced(x), filter(lambda data: data.get('synced') == 0, records)))
        _logger.info('--v--Creation--v--')
        _logger.info(results)
        return results
    
    def to_be_updated(self, records):
        _logger = logging.getLogger(__name__)
        results = list(map(lambda x: x, filter(lambda data: data.get('synced') == 2, records)))
        # results = list(map(lambda x: self.update_to_synced(x), filter(lambda data: data.get('synced') == 2, records)))
        _logger.info('--v--Updates--v--')
        _logger.info(results)
        return results
    
    def update_to_synced(self, data):
        data['synced'] = 1
        return data
    
    def removed_id(self, data):
        del data['id']
        return data

    # Models
    def getVehicle(self, raw_vehicle, obj_name):
        _logger = logging.getLogger(__name__)
        # if obj_name == 'vehicles':
        #     return {
        #         'id': raw_vehicle.get('id'),
        #         'state_id': raw_vehicle.get('state_id'),
        #         'company_id': raw_vehicle.get('company_id'),
        #         'synced': raw_vehicle.get('synced'),
        #         'model_id': raw_vehicle.get('model_id'),
        #         'license_plate': raw_vehicle.get('license_plate'),
        #         'tag_ids': raw_vehicle.get('tag_ids'),
        #         'active': raw_vehicle.get('active'),
        #         'driver_id': raw_vehicle.get('driver_id'),
        #         'future_driver_id': raw_vehicle.get('future_driver_id'),
        #         'plan_to_change_car': raw_vehicle.get('plan_to_change_car'),
        #         'plan_to_change_bike': raw_vehicle.get('plan_to_change_bike'),
        #         'next_assignation_date': raw_vehicle.get('next_assignation_date'),
        #         'category_id': raw_vehicle.get('category_id'),
        #         'order_date': raw_vehicle.get('order_date'),
        #         'acquisition_date': raw_vehicle.get('acquisition_date'),
        #         'write_off_date': raw_vehicle.get('write_off_date'),
        #         'vin_sn': raw_vehicle.get('vin_sn'),
        #         'odometer': raw_vehicle.get('odometer'),
        #         'odometer_unit': raw_vehicle.get('odometer_unit'),
        #         'manager_id': raw_vehicle.get('manager_id'),
        #         'location': raw_vehicle.get('location'),
        #         'vehicle_properties': raw_vehicle.get('vehicle_properties'),
        #         'horsepower_tax': raw_vehicle.get('horsepower_tax'),
        #         'first_contract_date': raw_vehicle.get('first_contract_date'),
        #         'car_value': raw_vehicle.get('car_value'),
        #         'net_car_value': raw_vehicle.get('net_car_value'),
        #         'residual_value': raw_vehicle.get('residual_value'),
        #         'model_year': raw_vehicle.get('model_year'),
        #         'transmission': raw_vehicle.get('transmission'),
        #         'color': raw_vehicle.get('color'),
        #         'seats': raw_vehicle.get('seats'),
        #         'doors': raw_vehicle.get('doors'),
        #         'trailer_hook': raw_vehicle.get('trailer_hook'),
        #         'frame_type': raw_vehicle.get('frame_type'),
        #         'frame_size': raw_vehicle.get('frame_size'),
        #         'electric_assistance': raw_vehicle.get('electric_assistance'),
        #         'horsepower': raw_vehicle.get('horsepower'),
        #         'power': raw_vehicle.get('power'),
        #         'fuel_type': raw_vehicle.get('fuel_type'),
        #         'co2': raw_vehicle.get('co2'),
        #         'co2_standard': raw_vehicle.get('co2_standard'),
        #         'description': raw_vehicle.get('description'),
        #         'driver_employee_id': raw_vehicle.get('driver_employee_id'),
        #         'future_driver_employee_id': raw_vehicle.get('future_driver_employee_id'),
        #     }
        # if obj_name == 'manufacturers':
        #     return {
        #         'id': raw_vehicle.get('id'),
        #         'name': raw_vehicle.get('name'),
        #         'active': raw_vehicle.get('active'),
        #     }
        # if obj_name == 'categories':
        #     return {
        #         'id': raw_vehicle.get('id'),
        #         'name': raw_vehicle.get('name'),
        #         'sequence': raw_vehicle.get('sequence'),
        #     }
        # if obj_name == 'models':
        #     return {
        #         'id': raw_vehicle.get('id'),
        #         'name': raw_vehicle.get('name'),
        #         'brand_id': raw_vehicle.get('brand_id'),
        #         'category_id': raw_vehicle.get('category_id'),
        #         'vehicle_type': raw_vehicle.get('vehicle_type'),
        #         'transmission': raw_vehicle.get('transmission'),
        #         'model_year': raw_vehicle.get('model_year'),
        #         'color': raw_vehicle.get('color'),
        #         'seats': raw_vehicle.get('seats'),
        #         'doors': raw_vehicle.get('doors'),
        #         'trailer_hook': raw_vehicle.get('trailer_hook'),
        #         'default_co2': raw_vehicle.get('default_co2'),
        #         'co2_standard': raw_vehicle.get('co2_standard'),
        #         'default_fuel_type': raw_vehicle.get('default_fuel_type'),
        #         'power': raw_vehicle.get('power'),
        #         'horsepower': raw_vehicle.get('horsepower'),
        #         'horsepower_tax': raw_vehicle.get('horsepower_tax'),
        #         'electric_assistance': raw_vehicle.get('electric_assistance'),
        #         'vehicle_properties_definition': raw_vehicle.get('vehicle_properties_definition'),
        #         'synced': raw_vehicle.get('synced'),
        #         'active': raw_vehicle.get('active'),
        #     }
        if obj_name == 'odometers':
            return {
                'id': raw_vehicle.get('id'),
                'name': raw_vehicle.get('name'),
                'datetime': raw_vehicle.get('datetime'),
                'odometer_start': raw_vehicle.get('odometer_start'),
                'odometer_end': raw_vehicle.get('odometer_end'),
                'bucket_amount': raw_vehicle.get('bucket_amount'),
                'loading_weight': raw_vehicle.get('loading_weight'),
                'total': raw_vehicle.get('total'),
                'value': raw_vehicle.get('value'),
                'vehicle_id': raw_vehicle.get('vehicle_id'),
                'unit': raw_vehicle.get('unit'),
                'driver_id': raw_vehicle.get('driver_id'),
                'synced': raw_vehicle.get('synced'),
            }
        if obj_name == 'petrols':
            return {
                'id': raw_vehicle.get('id'),
                'name': raw_vehicle.get('name'),
                'datetime': raw_vehicle.get('datetime'),
                'odometer': raw_vehicle.get('odometer'),
                'petrol': raw_vehicle.get('petrol'),
                'vehicle_id': raw_vehicle.get('vehicle_id'),
                'driver_id': raw_vehicle.get('driver_id'),
                'synced': raw_vehicle.get('synced'),
            }
        return {}
    
    def getIndexes_getList(self):
        return [
            # {
            #     'name': 'manufacturers',
            #     'data': http.request.env['fleet.vehicle.model.brand'].search_read([('synced', '!=', 1)])
            # },
            # {
            #     'name': 'categories',
            #     'data': http.request.env['fleet.vehicle.model.category'].search_read([('synced', '!=', 1)])
            # },
            # {
            #     'name': 'models',
            #     'data': http.request.env['fleet.vehicle.model'].search_read([('synced', '!=', 1)])
            # },
            # {
            #     'name': 'vehicles',
            #     'data': http.request.env['fleet.vehicle'].search_read([('synced', '!=', 1)])
            # },
            {
                'name': 'odometers',
                'data': http.request.env['fleet.vehicle.odometer'].search_read([('synced', '!=', 1)])
            },
            {
                'name': 'petrols',
                'data': http.request.env['fleet.vehicle.petrol'].search_read([('synced', '!=', 1)])
            },
        ]

    def getIndexes_withReqEnv(self, data):
        return [
            # {
            #     # Manufacturer (fleet.vehicle.model.brand)
            #     'json_name': 'manufacturers',
            #     'data': data.get('manufacturers'), 
            #     'request_env': http.request.env['fleet.vehicle.model.brand']
            # },
            # {
            #     # Model (fleet.vehicle.model.category)
            #     'json_name': 'categories',
            #     'data': data.get('categories'), 
            #     'request_env': http.request.env['fleet.vehicle.model.category']
            # },
            # {
            #     # Model (fleet.vehicle.model)
            #     'json_name': 'models',
            #     'data': data.get('models'), 
            #     'request_env': http.request.env['fleet.vehicle.model']
            # },
            # {
            #     # Vehicles (fleet.vehicle)
            #     'json_name': 'vehicles',
            #     'data': data.get('vehicles'), 
            #     'request_env': http.request.env['fleet.vehicle']
            # },
            {
                # Vehicles (fleet.vehicle.odometer)
                'json_name': 'odometers',
                'data': data.get('odometers'), 
                'request_env': http.request.env['fleet.vehicle.odometer']
            },
            {
                # Vehicles (fleet.vehicle.petrol)
                'json_name': 'petrols',
                'data': data.get('petrols'), 
                'request_env': http.request.env['fleet.vehicle.petrol']
            },
        ]