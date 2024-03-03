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
            "db": "sddb",
            "login": "techadmin",
            "password": "123asdASD!@#",    
        }

        data = self.getData()
        
        _logger.info(data)

        headers = {'Content-type': 'application/json'}      
        AUTH_URL = "http://3.26.69.148:8069/web/session/authenticate/"
        data = {
                "jsonrpc": "2.0",
                "params": {
                        "login": parameter['login'],
                        "password": parameter['password'],
                        "db": parameter['db'],
                        "data": data
                    }
                }  
        try:
            res = requests.post(AUTH_URL, data=json.dumps(data, default=str),headers=headers)
        except requests.exceptions.RequestException as e: 
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': ('Internet connection issue. Please check your connection. '),
                    'message': 'Something went wrong with the connection, please check your Wifi is connecting normally',
                    'type':'error',  #types: success,warning,danger,info
                    'sticky': False,  #True/False will display for few seconds if false
                    'fadeout': 'slow',
                },
            }
        _logger.info(res)
        _logger.info(res.cookies["session_id"])
        session_id = res.cookies["session_id"]
        base_url = "3.26.69.148:8069/api_controller/api_controller/sync_data" # your api 
        json_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            }
        cookies = {
            'login': "techadmin", 
            'password': '123asdASD!@#',
            'session_id':session_id
            }
        try:
            response = requests.post("http://{}".format(base_url), data = json.dumps(data, default=str), headers=json_headers, cookies=cookies)
        except requests.exceptions.RequestException as e: 
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': ('Internet connection issue. Please check your connection. '),
                    'message': 'Something went wrong with the connection, please check your Wifi is connecting normally',
                    'type':'error',  #types: success,warning,danger,info
                    'sticky': False,  #True/False will display for few seconds if false
                    'fadeout': 'slow',
                },
            }
        _logger.info(response.status_code)
        _logger.info(response.json().get('result'))
        self.Synced()
        return self.updateMasterData(response.json().get('result'))
        
    
    def getData(self):
        _logger = logging.getLogger(__name__)
        indexes = self.getIndexes_getList()

        indexes = self.mapValueToProcessable(indexes)
        # for index in indexes:
        #     index['data'] = self.mapValueToProcessable(index.get('data'))
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
            # 'odometers': list(filter(lambda x: x.get('name') == 'odometers', indexes))[0].get('data'),
            # 'petrols': list(filter(lambda x: x.get('name') == 'petrols', indexes))[0].get('data'),
            'trips': list(filter(lambda x: x.get('name') == 'trips', indexes))[0].get('data'),
        }
        
        testServerSideResult = {
            'manufacturers': [],
            'categories': [],
            'models': [],
            'vehicles': [],
        }
        _logger.info(result)
        return result
    
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
                        if x == 'synced':
                            data[x] = True
                        if x == 'vehicle_id':
                            data[x] = http.request.env['fleet.vehicle'].search([('id', '=', data[x])]).ex_id
                        if x == 'driver_id':
                            data[x] = http.request.env['res.partner'].search([('id', '=', data[x])]).ex_id
                        if x == 'trip_id':
                            data[x] = http.request.env['fleet.vehicle.trip.master'].search([('id', '=', data[x])]).ex_id
                        continue
        return masterDataList
    
    def updateMasterData(self, data):
        if not data:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': ('Opps.. Seems like something went wrong. '),
                    'message': 'Please contact administrator to fix the problem',
                    'type':'error',  #types: success,warning,danger,info
                    'sticky': False,  #True/False will display for few seconds if false
                    'fadeout': 'slow',
                },
            }
        _logger = logging.getLogger(__name__)
        for item in data:
            _logger.info('updating ' + item.get('name'))
            masterData = list(filter(lambda x: x.get('name') == item.get('name'), self.masterDataList()))
            _logger.info('masterData')
            _logger.info( masterData)
            if (len(masterData) > 0):
                env = masterData[0].get('env')
                recordsData = item.get('data')
                _logger.info('recordsData ')
                _logger.info(recordsData)
                for rawrecordData in recordsData:
                    recordData = self.getObjectForCRUD(rawrecordData, item.get('name'), False)
                    existingRecord = env.search([('name', '=', recordData.get('name'))])
                    _logger.info('existingRecord ')
                    _logger.info(existingRecord)
                    if existingRecord:
                        existingRecord.write(recordData)
                    else:
                        newRecord = env.sudo().create(recordData)
                    if item.get('create_multi') == False:
                        self.env.cr.commit()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': ('Synchronize Successfully'),
                'message': 'You have successfully synchronized with the cloud',
                'type':'success',  #types: success,warning,danger,info
                'sticky': False,  #True/False will display for few seconds if false
                'fadeout': 'slow',
                'next': {
                    'type': 'ir.actions.act_window_close',
                }
            },
        }
    
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
        return data
    
    def Synced(self):
        unsyncedData = http.request.env['fleet.vehicle.trip'].search([('synced', '!=', 1)])
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
    def getObjectForCRUD(self, raw_data, obj_name, isUpToServer):
        _logger = logging.getLogger(__name__)
        model_env = http.request.env['fleet.vehicle.model']
        brand_env = http.request.env['fleet.vehicle.model.brand']
        vehicle_env = http.request.env['fleet.vehicle']
        vehicle_category_env = http.request.env['fleet.vehicle.model.category']
        vehicle_state_env = http.request.env['fleet.vehicle.state']
        trip_master_env = http.request.env['fleet.vehicle.trip.master']
        res_partner_env = http.request.env['res.partner']
        if obj_name == 'fleet.vehicle':
            return {
                'id': raw_data.get('id'),
                'ex_id': raw_data.get('ex_id'),
                'name': raw_data.get('name'),
                'state_id': vehicle_state_env.search([('id', '=', raw_data.get('state_id'))]).ex_id if isUpToServer else vehicle_state_env.search([('ex_id', '=', raw_data.get('state_id'))]).id,
                'company_id': raw_data.get('company_id'),
                'synced': raw_data.get('synced'),
                'model_id': model_env.search([('id', '=', raw_data.get('model_id'))]).ex_id if isUpToServer else model_env.search([('ex_id', '=', raw_data.get('model_id'))]).id,
                'license_plate': raw_data.get('license_plate'),
                'tag_ids': raw_data.get('tag_ids'),
                'active': raw_data.get('active'),
                'driver_id': res_partner_env.search([('id', '=', raw_data.get('driver_id'))]).ex_id if isUpToServer else res_partner_env.search([('ex_id', '=', raw_data.get('driver_id'))]).id,
                'future_driver_id': raw_data.get('future_driver_id'),
                'plan_to_change_car': raw_data.get('plan_to_change_car'),
                'plan_to_change_bike': raw_data.get('plan_to_change_bike'),
                'next_assignation_date': raw_data.get('next_assignation_date'),
                'category_id': vehicle_category_env.search([('id', '=', raw_data.get('category_id'))]).ex_id if isUpToServer else vehicle_category_env.search([('ex_id', '=', raw_data.get('category_id'))]).id,
                'order_date': raw_data.get('order_date'),
                'acquisition_date': raw_data.get('acquisition_date'),
                'write_off_date': raw_data.get('write_off_date'),
                'vin_sn': raw_data.get('vin_sn'),
                'odometer': raw_data.get('odometer'),
                'initial_odometer': raw_data.get('initial_odometer'),
                'odometer_unit': raw_data.get('odometer_unit'),
                'manager_id': raw_data.get('manager_id'),
                'location': raw_data.get('location'),
                'vehicle_properties': raw_data.get('vehicle_properties'),
                'horsepower_tax': raw_data.get('horsepower_tax'),
                'first_contract_date': raw_data.get('first_contract_date'),
                'car_value': raw_data.get('car_value'),
                'net_car_value': raw_data.get('net_car_value'),
                'residual_value': raw_data.get('residual_value'),
                'model_year': raw_data.get('model_year'),
                'transmission': raw_data.get('transmission'),
                'color': raw_data.get('color'),
                'seats': raw_data.get('seats'),
                'doors': raw_data.get('doors'),
                'trailer_hook': raw_data.get('trailer_hook'),
                'frame_type': raw_data.get('frame_type'),
                'frame_size': raw_data.get('frame_size'),
                'electric_assistance': raw_data.get('electric_assistance'),
                'horsepower': raw_data.get('horsepower'),
                'power': raw_data.get('power'),
                'fuel_type': raw_data.get('fuel_type'),
                'co2': raw_data.get('co2'),
                'co2_standard': raw_data.get('co2_standard'),
                'description': raw_data.get('description'),
            }
        if obj_name == 'fleet.vehicle.model.brand':
            return {
                'id': raw_data.get('id'),
                'ex_id': raw_data.get('ex_id'),
                'name': raw_data.get('name'),
                'active': raw_data.get('active'),
            }
        if obj_name == 'fleet.vehicle.model.category':
            return {
                'id': raw_data.get('id'),
                'ex_id': raw_data.get('ex_id'),
                'name': raw_data.get('name'),
                'sequence': raw_data.get('sequence'),
            }
        if obj_name == 'fleet.vehicle.model':
            return {
                'id': raw_data.get('id'),
                'ex_id': raw_data.get('ex_id'),
                'name': raw_data.get('name'),
                'brand_id': brand_env.search([('id', '=', raw_data.get('brand_id'))]).ex_id if isUpToServer else brand_env.search([('ex_id', '=', raw_data.get('brand_id'))]).id,
                'category_id': raw_data.get('category_id'),
                'vehicle_type': raw_data.get('vehicle_type'),
                'transmission': raw_data.get('transmission'),
                'model_year': raw_data.get('model_year'),
                'color': raw_data.get('color'),
                'seats': raw_data.get('seats'),
                'doors': raw_data.get('doors'),
                'trailer_hook': raw_data.get('trailer_hook'),
                'default_co2': raw_data.get('default_co2'),
                'co2_standard': raw_data.get('co2_standard'),
                'default_fuel_type': raw_data.get('default_fuel_type'),
                'power': raw_data.get('power'),
                'horsepower': raw_data.get('horsepower'),
                'horsepower_tax': raw_data.get('horsepower_tax'),
                'electric_assistance': raw_data.get('electric_assistance'),
                'vehicle_properties_definition': raw_data.get('vehicle_properties_definition'),
                'synced': raw_data.get('synced'),
                'active': raw_data.get('active'),
            }
        if obj_name == 'res.partner':
            return {
                'id': raw_data.get('id'),
                'ex_id': raw_data.get('ex_id'),
                'name': raw_data.get('name'),
                'type': raw_data.get('type'),
                'street': raw_data.get('street'),
                'street2': raw_data.get('street2'),
                'zip': raw_data.get('zip'),
                'city': raw_data.get('city'),
                'state_id': raw_data.get('state_id'),
                'country_id': raw_data.get('country_id'),
                'function': raw_data.get('function'),
                'vat': raw_data.get('vat'),
                'phone': raw_data.get('phone'),
                'mobile': raw_data.get('mobile'),
                'email': raw_data.get('email'),
                'title': raw_data.get('title'),
                'active': raw_data.get('active'),
            }
        if obj_name == 'fleet.vehicle.state':
            return {
                'id': raw_data.get('id'),
                'ex_id': raw_data.get('ex_id'),
                'name': raw_data.get('name'),
                'sequence': raw_data.get('sequence'),
                'visibility': raw_data.get('visibility'),
            }
        if obj_name == 'fleet.vehicle.trip.master':
            return {
                'id': raw_data.get('id'),
                'ex_id': raw_data.get('ex_id'),
                'name': raw_data.get('name'),
                'distance': raw_data.get('distance'),
                'price': raw_data.get('price'),
                'bucket': raw_data.get('bucket'),
                'weight': raw_data.get('weight'),
            }
        # if obj_name == 'odometers':
        #     return {
        #         'id': raw_data.get('id'),
        #         'name': raw_data.get('name'),
        #         'datetime': raw_data.get('datetime'),
        #         'odometer_start': raw_data.get('odometer_start'),
        #         'odometer_end': raw_data.get('odometer_end'),
        #         'bucket_amount': raw_data.get('bucket_amount'),
        #         'loading_weight': raw_data.get('loading_weight'),
        #         'total': raw_data.get('total'),
        #         'value': raw_data.get('value'),
        #         'vehicle_id': raw_data.get('vehicle_id'),
        #         'unit': raw_data.get('unit'),
        #         'driver_id': raw_data.get('driver_id'),
        #         'synced': raw_data.get('synced'),
        #     }
        # if obj_name == 'petrols':
        #     return {
        #         'id': raw_data.get('id'),
        #         'name': raw_data.get('name'),
        #         'datetime': raw_data.get('datetime'),
        #         'odometer': raw_data.get('odometer'),
        #         'petrol': raw_data.get('petrol'),
        #         'vehicle_id': raw_data.get('vehicle_id'),
        #         'driver_id': raw_data.get('driver_id'),
        #         'synced': raw_data.get('synced'),
        #     }
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
            # {
            #     'name': 'odometers',
            #     'data': http.request.env['fleet.vehicle.odometer'].search_read([('synced', '!=', 1)])
            # },
            # {
            #     'name': 'petrols',
            #     'data': http.request.env['fleet.vehicle.petrol'].search_read([('synced', '!=', 1)])
            # },
            {
                'name': 'trips',
                'data': http.request.env['fleet.vehicle.trip'].search_read([('synced', '!=', 1)])
            },
        ]
        
    # manual sequence, please add from parent to child accordingly
    def masterDataList(self):
        return [
            {
                'name': 'res.partner',
                'env': http.request.env['res.partner'],
                'create_multi': False
            },
            {
                'name': 'fleet.vehicle.state',
                'env': http.request.env['fleet.vehicle.state'],
                'create_multi': False
            },
            {
                'name': 'fleet.vehicle.model.category',
                'env': http.request.env['fleet.vehicle.model.category'],
                'create_multi': False
            },
            {
                'name': 'fleet.vehicle.model.brand',
                'env': http.request.env['fleet.vehicle.model.brand'],
                'create_multi': False
            },
            {
                'name': 'fleet.vehicle.model',
                'env': http.request.env['fleet.vehicle.model'],
                'create_multi': False
            },
            {
                'name': 'fleet.vehicle',
                'env': http.request.env['fleet.vehicle'],
                'create_multi': True
            },
            {
                'name': 'fleet.vehicle.trip.master',
                'env': http.request.env['fleet.vehicle.trip.master'],
                'create_multi': False
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