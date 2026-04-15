"""车辆与司机管理控制器。"""

from flask import request, jsonify
from flask_jwt_extended import get_jwt_identity
from flask_bcrypt import generate_password_hash
from models.index import db, Vehicle, User, RoleEnum, CarApplication, Dispatch


LOCKED_APPLICATION_STATUSES = ['pending', 'approved', 'dispatched']


def _build_username(phone):
    base = str(phone)
    candidate = base
    suffix = 1
    while User.query.filter_by(username=candidate).first():
        suffix += 1
        candidate = f'{base}_{suffix}'
    return candidate


def _enum_value(value):
    return value.value if hasattr(value, 'value') else value


def _driver_is_locked(driver_user_id, exclude_application_id=None):
    query = CarApplication.query.filter(
        CarApplication.driver_id == driver_user_id,
        CarApplication.status.in_(LOCKED_APPLICATION_STATUSES)
    )
    if exclude_application_id:
        query = query.filter(CarApplication.id != exclude_application_id)
    return query.first() is not None


def _driver_has_active_dispatch(driver_user_id):
    return Dispatch.query.filter(
        Dispatch.driver_id == driver_user_id,
        Dispatch.status.in_(['scheduled', 'in_progress'])
    ).first() is not None


def _vehicle_has_active_dispatch(vehicle_id):
    return Dispatch.query.filter(
        Dispatch.vehicle_id == vehicle_id,
        Dispatch.status.in_(['scheduled', 'in_progress'])
    ).first() is not None


def _driver_to_dict(driver_user):
    payload = driver_user.to_dict()
    vehicle = Vehicle.query.get(driver_user.vehicle_id) if driver_user.vehicle_id else None
    payload['status'] = driver_user.driver_status.value if driver_user.driver_status else None
    payload['vehicle_plate_number'] = vehicle.plate_number if vehicle else None
    payload['vehicle_status'] = _enum_value(vehicle.status) if vehicle else None
    payload['user_id'] = driver_user.id
    payload['locked_by_application'] = _driver_is_locked(driver_user.id)
    return payload


# ==================== 车辆接口 ====================

def get_vehicles():
    try:
        vehicles = Vehicle.query.filter_by(is_deleted=False).all()
        return jsonify({'success': True, 'data': [vehicle.to_dict() for vehicle in vehicles]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


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
        next_status = data.get('status', vehicle.status)
        if next_status != vehicle.status and _vehicle_has_active_dispatch(vehicle.id):
            return jsonify({'success': False, 'message': '车辆已被调度，结束行程前不能修改状态'}), 400
        vehicle.status = next_status
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


def delete_vehicle(id):
    try:
        vehicle = Vehicle.query.get(id)
        if not vehicle or vehicle.is_deleted:
            return jsonify({'success': False, 'message': '车辆不存在'})

        bound_driver = User.query.filter_by(role=RoleEnum.driver, vehicle_id=id, is_deleted=False).first()
        if bound_driver:
            return jsonify({'success': False, 'message': '该车辆已绑定司机，不能删除'}), 400

        vehicle.is_deleted = True
        vehicle.deleted_at = db.func.now()
        vehicle.deleted_by = get_jwt_identity()
        db.session.commit()
        return jsonify({'success': True, 'message': '车辆删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


# ==================== 司机接口（基于 users.role=driver） ====================

def get_drivers():
    try:
        drivers = User.query.filter_by(role=RoleEnum.driver, is_deleted=False).all()
        return jsonify({'success': True, 'data': [_driver_to_dict(driver) for driver in drivers]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


def create_driver():
    try:
        data = request.json or {}
        required_fields = ['name', 'phone', 'license_number', 'vehicle_id']
        missing = [field for field in required_fields if data.get(field) in [None, '']]
        if missing:
            return jsonify({'success': False, 'message': f'缺少必填字段: {", ".join(missing)}'}), 400

        phone = str(data['phone']).strip()
        license_number = str(data['license_number']).strip()
        vehicle_id = int(data['vehicle_id'])

        if User.query.filter_by(phone=phone, is_deleted=False).first():
            return jsonify({'success': False, 'message': '手机号已存在'}), 400

        if User.query.filter_by(license_number=license_number, is_deleted=False).first():
            return jsonify({'success': False, 'message': '驾驶证号已存在'}), 400

        vehicle = Vehicle.query.get(vehicle_id)
        if not vehicle or vehicle.is_deleted:
            return jsonify({'success': False, 'message': '绑定车辆不存在'}), 400

        if User.query.filter_by(role=RoleEnum.driver, vehicle_id=vehicle_id, is_deleted=False).first():
            return jsonify({'success': False, 'message': '该车辆已被其他司机绑定'}), 400

        driver = User(
            username=_build_username(phone),
            password=generate_password_hash(phone).decode('utf-8'),
            name=str(data['name']).strip(),
            phone=phone,
            role=RoleEnum.driver,
            vehicle_id=vehicle_id,
            license_number=license_number,
            driver_status=data.get('status', 'available'),
            hire_date=data.get('hire_date'),
            must_change_password=True,
            created_by=get_jwt_identity()
        )
        db.session.add(driver)
        db.session.commit()
        return jsonify({'success': True, 'data': _driver_to_dict(driver)})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


def update_driver(id):
    try:
        driver = User.query.filter_by(id=id, role=RoleEnum.driver, is_deleted=False).first()
        if not driver:
            return jsonify({'success': False, 'message': '司机不存在'})

        data = request.json or {}

        if data.get('vehicle_id') is not None and int(data.get('vehicle_id')) != int(driver.vehicle_id or 0):
            vehicle_id = int(data.get('vehicle_id'))
            vehicle = Vehicle.query.get(vehicle_id)
            if not vehicle or vehicle.is_deleted:
                return jsonify({'success': False, 'message': '绑定车辆不存在'}), 400
            existing = User.query.filter(
                User.role == RoleEnum.driver,
                User.vehicle_id == vehicle_id,
                User.id != id,
                User.is_deleted == False
            ).first()
            if existing:
                return jsonify({'success': False, 'message': '该车辆已被其他司机绑定'}), 400
            driver.vehicle_id = vehicle_id

        new_status = data.get('status')
        if new_status and new_status != _enum_value(driver.driver_status) and _driver_has_active_dispatch(driver.id):
            return jsonify({'success': False, 'message': '司机已被调度，结束行程前不能修改状态'}), 400

        if new_status == 'available' and _driver_is_locked(driver.id):
            return jsonify({'success': False, 'message': '司机有进行中的申请，不能设置为可用'}), 400

        if data.get('phone') and data.get('phone') != driver.phone:
            if User.query.filter(User.phone == data.get('phone'), User.id != id, User.is_deleted == False).first():
                return jsonify({'success': False, 'message': '手机号已存在'}), 400
            driver.phone = data.get('phone')

        if data.get('license_number') and data.get('license_number') != driver.license_number:
            if User.query.filter(User.license_number == data.get('license_number'), User.id != id, User.is_deleted == False).first():
                return jsonify({'success': False, 'message': '驾驶证号已存在'}), 400
            driver.license_number = data.get('license_number')

        driver.name = data.get('name', driver.name)
        driver.driver_status = new_status or driver.driver_status
        driver.hire_date = data.get('hire_date', driver.hire_date)

        db.session.commit()
        return jsonify({'success': True, 'data': _driver_to_dict(driver)})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


def delete_driver(id):
    try:
        driver = User.query.filter_by(id=id, role=RoleEnum.driver, is_deleted=False).first()
        if not driver:
            return jsonify({'success': False, 'message': '司机不存在'})

        if _driver_is_locked(id):
            return jsonify({'success': False, 'message': '司机有进行中的申请，不能删除'}), 400

        driver.is_deleted = True
        driver.is_active = False
        driver.deleted_at = db.func.now()
        driver.deleted_by = get_jwt_identity()
        db.session.commit()
        return jsonify({'success': True, 'message': '司机删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


def get_available_drivers():
    try:
        drivers = User.query.filter_by(role=RoleEnum.driver, driver_status='available', is_deleted=False).all()
        result = []
        for driver in drivers:
            vehicle = Vehicle.query.get(driver.vehicle_id) if driver.vehicle_id else None
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
