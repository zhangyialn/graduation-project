"""车辆与司机管理控制器。"""

# 车辆管理控制器
from flask import request, jsonify
from flask_jwt_extended import get_jwt_identity
from models.index import db, Vehicle, Driver, User, RoleEnum, CarApplication


LOCKED_APPLICATION_STATUSES = ['pending', 'approved', 'dispatched']


# 兼容 Enum/字符串状态读取
def _enum_value(value):
    return value.value if hasattr(value, 'value') else value


# 判断司机是否被进行中的申请占用
def _driver_is_locked(driver_id, exclude_application_id=None):
    query = CarApplication.query.filter(
        CarApplication.driver_id == driver_id,
        CarApplication.status.in_(LOCKED_APPLICATION_STATUSES)
    )
    if exclude_application_id:
        query = query.filter(CarApplication.id != exclude_application_id)
    return query.first() is not None


# 获取所有车辆
# 查询车辆列表（过滤软删除）
def get_vehicles():
    try:
        vehicles = Vehicle.query.filter_by(is_deleted=False).all()
        return jsonify({'success': True, 'data': [vehicle.to_dict() for vehicle in vehicles]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 获取单个车辆
# 查询单辆车详情
def get_vehicle(id):
    try:
        vehicle = Vehicle.query.get(id)
        if not vehicle or vehicle.is_deleted:
            return jsonify({'success': False, 'message': '车辆不存在'})
        return jsonify({'success': True, 'data': vehicle.to_dict()})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 创建车辆
# 创建车辆
def create_vehicle():
    try:
        data = request.json
        vehicle = Vehicle(
            plate_number=data['plate_number'],
            model=data['model'],
            brand=data['brand'],
            color=data['color'],
            seat_count=data.get('seat_count', 5),
            purchase_date=data['purchase_date'],
            fuel_type=data['fuel_type'],
            fuel_consumption_per_100km=data.get('fuel_consumption_per_100km'),
            annual_inspection_date=data.get('annual_inspection_date'),
            created_by=get_jwt_identity()
        )
        db.session.add(vehicle)
        db.session.commit()
        return jsonify({'success': True, 'data': vehicle.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


# 更新车辆
# 更新车辆信息
def update_vehicle(id):
    try:
        vehicle = Vehicle.query.get(id)
        if not vehicle or vehicle.is_deleted:
            return jsonify({'success': False, 'message': '车辆不存在'})

        data = request.json
        vehicle.plate_number = data.get('plate_number', vehicle.plate_number)
        vehicle.model = data.get('model', vehicle.model)
        vehicle.brand = data.get('brand', vehicle.brand)
        vehicle.color = data.get('color', vehicle.color)
        vehicle.status = data.get('status', vehicle.status)
        vehicle.fuel_type = data.get('fuel_type', vehicle.fuel_type)
        vehicle.seat_count = data.get('seat_count', vehicle.seat_count)
        vehicle.fuel_consumption_per_100km = data.get('fuel_consumption_per_100km', vehicle.fuel_consumption_per_100km)
        vehicle.annual_inspection_date = data.get('annual_inspection_date', vehicle.annual_inspection_date)
        vehicle.last_maintenance_date = data.get('last_maintenance_date', vehicle.last_maintenance_date)

        db.session.commit()
        return jsonify({'success': True, 'data': vehicle.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


# 删除车辆
# 软删除车辆（已绑定司机时不允许删除）
def delete_vehicle(id):
    try:
        vehicle = Vehicle.query.get(id)
        if not vehicle or vehicle.is_deleted:
            return jsonify({'success': False, 'message': '车辆不存在'})

        if Driver.query.filter_by(vehicle_id=id, is_deleted=False).first():
            return jsonify({'success': False, 'message': '该车辆已绑定司机，不能删除'}), 400

        vehicle.is_deleted = True
        vehicle.deleted_at = db.func.now()
        vehicle.deleted_by = get_jwt_identity()
        db.session.commit()
        return jsonify({'success': True, 'message': '车辆删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


# 获取可用车辆列表
# 查询可用车辆
def get_available_vehicles():
    try:
        vehicles = Vehicle.query.filter_by(status='available', is_deleted=False).all()
        return jsonify({'success': True, 'data': [vehicle.to_dict() for vehicle in vehicles]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# ==================== 司机管理接口 ====================

# 司机视图组装：附带用户信息、车辆信息、占用状态
def _driver_to_dict(driver):
    payload = driver.to_dict()
    vehicle = Vehicle.query.get(driver.vehicle_id) if driver.vehicle_id else None
    user = User.query.get(driver.user_id) if driver.user_id else None
    payload['vehicle_plate_number'] = vehicle.plate_number if vehicle else None
    payload['vehicle_status'] = _enum_value(vehicle.status) if vehicle else None
    payload['username'] = user.username if user else None
    payload['user_role'] = _enum_value(user.role) if user else None
    payload['locked_by_application'] = _driver_is_locked(driver.id)
    return payload


# 获取所有司机
# 查询司机列表
def get_drivers():
    try:
        drivers = Driver.query.filter_by(is_deleted=False).all()
        return jsonify({'success': True, 'data': [_driver_to_dict(driver) for driver in drivers]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 创建司机
# 创建司机档案并绑定用户/车辆
def create_driver():
    try:
        data = request.json

        required_fields = ['name', 'phone', 'license_number', 'user_id', 'vehicle_id']
        missing = [field for field in required_fields if data.get(field) in [None, '']]
        if missing:
            return jsonify({'success': False, 'message': f'缺少必填字段: {", ".join(missing)}'}), 400

        user = User.query.get(int(data['user_id']))
        if not user or user.is_deleted:
            return jsonify({'success': False, 'message': '绑定用户不存在'}), 400

        if _enum_value(user.role) != RoleEnum.driver.value:
            return jsonify({'success': False, 'message': '绑定用户角色必须为 driver'}), 400

        vehicle = Vehicle.query.get(int(data['vehicle_id']))
        if not vehicle or vehicle.is_deleted:
            return jsonify({'success': False, 'message': '绑定车辆不存在'}), 400

        if Driver.query.filter_by(user_id=int(data['user_id']), is_deleted=False).first():
            return jsonify({'success': False, 'message': '该用户已绑定司机档案'}), 400

        if Driver.query.filter_by(vehicle_id=int(data['vehicle_id']), is_deleted=False).first():
            return jsonify({'success': False, 'message': '该车辆已被其他司机绑定'}), 400

        driver = Driver(
            user_id=int(data['user_id']),
            vehicle_id=int(data['vehicle_id']),
            name=data['name'],
            phone=data['phone'],
            license_number=data['license_number'],
            hire_date=data.get('hire_date'),
            status=data.get('status', 'available'),
            created_by=get_jwt_identity()
        )
        db.session.add(driver)
        db.session.commit()
        return jsonify({'success': True, 'data': _driver_to_dict(driver)})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


# 更新司机
# 更新司机档案
def update_driver(id):
    try:
        driver = Driver.query.get(id)
        if not driver or driver.is_deleted:
            return jsonify({'success': False, 'message': '司机不存在'})

        data = request.json
        if data.get('user_id') is not None and int(data.get('user_id')) != driver.user_id:
            user = User.query.get(int(data.get('user_id')))
            if not user or user.is_deleted:
                return jsonify({'success': False, 'message': '绑定用户不存在'}), 400
            if _enum_value(user.role) != RoleEnum.driver.value:
                return jsonify({'success': False, 'message': '绑定用户角色必须为 driver'}), 400
            existing = Driver.query.filter(
                Driver.user_id == int(data.get('user_id')),
                Driver.id != id,
                Driver.is_deleted == False
            ).first()
            if existing:
                return jsonify({'success': False, 'message': '该用户已绑定其他司机档案'}), 400
            driver.user_id = int(data.get('user_id'))

        if data.get('vehicle_id') is not None and int(data.get('vehicle_id')) != driver.vehicle_id:
            vehicle = Vehicle.query.get(int(data.get('vehicle_id')))
            if not vehicle or vehicle.is_deleted:
                return jsonify({'success': False, 'message': '绑定车辆不存在'}), 400
            existing = Driver.query.filter(
                Driver.vehicle_id == int(data.get('vehicle_id')),
                Driver.id != id,
                Driver.is_deleted == False
            ).first()
            if existing:
                return jsonify({'success': False, 'message': '该车辆已被其他司机绑定'}), 400
            driver.vehicle_id = int(data.get('vehicle_id'))

        new_status = data.get('status')
        if new_status == 'available' and _driver_is_locked(driver.id):
            return jsonify({'success': False, 'message': '司机有进行中的申请，不能设置为可用'}), 400

        driver.name = data.get('name', driver.name)
        driver.phone = data.get('phone', driver.phone)
        driver.status = new_status or driver.status
        driver.hire_date = data.get('hire_date', driver.hire_date)

        db.session.commit()
        return jsonify({'success': True, 'data': _driver_to_dict(driver)})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


# 删除司机
# 软删除司机（存在进行中申请时不允许）
def delete_driver(id):
    try:
        driver = Driver.query.get(id)
        if not driver or driver.is_deleted:
            return jsonify({'success': False, 'message': '司机不存在'})

        if _driver_is_locked(id):
            return jsonify({'success': False, 'message': '司机有进行中的申请，不能删除'}), 400

        driver.is_deleted = True
        driver.deleted_at = db.func.now()
        driver.deleted_by = get_jwt_identity()
        db.session.commit()
        return jsonify({'success': True, 'message': '司机删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


# 获取可用司机列表
# 查询可分配司机（司机可用 + 车辆可用 + 无进行中申请）
def get_available_drivers():
    try:
        drivers = Driver.query.filter_by(status='available', is_deleted=False).all()
        result = []
        for driver in drivers:
            vehicle = Vehicle.query.get(driver.vehicle_id)
            if not vehicle or vehicle.is_deleted:
                continue
            if _enum_value(vehicle.status) != 'available':
                continue
            if _driver_is_locked(driver.id):
                continue
            result.append(_driver_to_dict(driver))
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
