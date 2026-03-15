# 车辆和司机管理控制器
from flask import request, jsonify
from models.index import db, Vehicle, Driver


# 获取所有车辆
def get_vehicles():
    try:
        vehicles = Vehicle.query.all()
        return jsonify({'success': True, 'data': [vehicle.to_dict() for vehicle in vehicles]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 获取单个车辆
def get_vehicle(id):
    try:
        vehicle = Vehicle.query.get(id)
        if not vehicle:
            return jsonify({'success': False, 'message': '车辆不存在'})
        return jsonify({'success': True, 'data': vehicle.to_dict()})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 创建车辆
def create_vehicle():
    try:
        data = request.json
        vehicle = Vehicle(
            plate_number=data['plate_number'],
            model=data['model'],
            brand=data['brand'],
            color=data['color'],
            purchase_date=data['purchase_date'],
            fuel_type=data['fuel_type']
        )
        db.session.add(vehicle)
        db.session.commit()
        return jsonify({'success': True, 'data': vehicle.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


# 更新车辆
def update_vehicle(id):
    try:
        vehicle = Vehicle.query.get(id)
        if not vehicle:
            return jsonify({'success': False, 'message': '车辆不存在'})
        
        data = request.json
        vehicle.plate_number = data.get('plate_number', vehicle.plate_number)
        vehicle.model = data.get('model', vehicle.model)
        vehicle.brand = data.get('brand', vehicle.brand)
        vehicle.color = data.get('color', vehicle.color)
        vehicle.status = data.get('status', vehicle.status)
        vehicle.fuel_type = data.get('fuel_type', vehicle.fuel_type)
        
        db.session.commit()
        return jsonify({'success': True, 'data': vehicle.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


# 删除车辆
def delete_vehicle(id):
    try:
        vehicle = Vehicle.query.get(id)
        if not vehicle:
            return jsonify({'success': False, 'message': '车辆不存在'})
        
        db.session.delete(vehicle)
        db.session.commit()
        return jsonify({'success': True, 'message': '车辆删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


# 获取可用车辆列表
def get_available_vehicles():
    try:
        vehicles = Vehicle.query.filter_by(status='available').all()
        return jsonify({'success': True, 'data': [vehicle.to_dict() for vehicle in vehicles]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# ==================== 司机管理接口 ====================

# 获取所有司机
def get_drivers():
    try:
        drivers = Driver.query.all()
        return jsonify({'success': True, 'data': [driver.to_dict() for driver in drivers]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 创建司机
def create_driver():
    try:
        data = request.json
        driver = Driver(
            name=data['name'],
            phone=data['phone'],
            license_number=data['license_number']
        )
        db.session.add(driver)
        db.session.commit()
        return jsonify({'success': True, 'data': driver.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


# 更新司机
def update_driver(id):
    try:
        driver = Driver.query.get(id)
        if not driver:
            return jsonify({'success': False, 'message': '司机不存在'})
        
        data = request.json
        driver.name = data.get('name', driver.name)
        driver.phone = data.get('phone', driver.phone)
        driver.status = data.get('status', driver.status)
        
        db.session.commit()
        return jsonify({'success': True, 'data': driver.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


# 删除司机
def delete_driver(id):
    try:
        driver = Driver.query.get(id)
        if not driver:
            return jsonify({'success': False, 'message': '司机不存在'})
        
        db.session.delete(driver)
        db.session.commit()
        return jsonify({'success': True, 'message': '司机删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


# 获取可用司机列表
def get_available_drivers():
    try:
        drivers = Driver.query.filter_by(status='available').all()
        return jsonify({'success': True, 'data': [driver.to_dict() for driver in drivers]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})