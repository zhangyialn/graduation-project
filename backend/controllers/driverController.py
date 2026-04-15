"""司机工作台控制器。"""

from flask import request, jsonify
from flask_jwt_extended import get_jwt_identity
from models.index import db, Dispatch, Vehicle, User, RoleEnum
from controllers.common_helpers import enum_value as _enum_value
from services.driver_dashboard_service import build_driver_dashboard


def _get_current_driver_user():
    current_user_id = get_jwt_identity()
    user = User.query.filter_by(id=current_user_id, role=RoleEnum.driver, is_deleted=False).first()
    return user, current_user_id


def get_my_dashboard():
    try:
        driver, _current_user_id = _get_current_driver_user()
        if not driver:
            return jsonify({'success': False, 'message': '当前账号不是司机账号'}), 404
        dashboard_payload = build_driver_dashboard(driver)

        db.session.commit()

        return jsonify({
            'success': True,
            'data': dashboard_payload
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


def update_my_status():
    try:
        driver, _current_user_id = _get_current_driver_user()
        if not driver:
            return jsonify({'success': False, 'message': '当前账号不是司机账号'}), 404

        data = request.json or {}
        status = data.get('status')
        if status not in ['available', 'unavailable']:
            return jsonify({'success': False, 'message': '司机状态仅支持 available/unavailable'}), 400

        active_dispatch = Dispatch.query.filter(
            Dispatch.driver_id == driver.id,
            Dispatch.status.in_(['scheduled', 'in_progress'])
        ).first()
        if active_dispatch and status != _enum_value(driver.driver_status):
            return jsonify({'success': False, 'message': '司机已被调度，结束行程前不能修改状态'}), 400

        if status == 'available':
            if active_dispatch:
                return jsonify({'success': False, 'message': '司机存在进行中的任务，不能设为可用'}), 400

        driver.driver_status = status
        db.session.commit()
        return jsonify({'success': True, 'data': driver.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


def update_my_vehicle_status():
    try:
        driver, _current_user_id = _get_current_driver_user()
        if not driver:
            return jsonify({'success': False, 'message': '当前账号不是司机账号'}), 404

        data = request.json or {}
        status = data.get('status')
        if status not in ['available', 'maintenance', 'unavailable']:
            return jsonify({'success': False, 'message': '车辆状态仅支持 available/maintenance/unavailable'}), 400

        vehicle = Vehicle.query.get(driver.vehicle_id)
        if not vehicle or vehicle.is_deleted:
            return jsonify({'success': False, 'message': '绑定车辆不存在'}), 404

        active_dispatch = Dispatch.query.filter(
            Dispatch.driver_id == driver.id,
            Dispatch.status.in_(['scheduled', 'in_progress'])
        ).first()
        if active_dispatch and status != _enum_value(vehicle.status):
            return jsonify({'success': False, 'message': '司机已被调度，结束行程前不能修改车辆状态'}), 400

        if status == 'available':
            if active_dispatch:
                return jsonify({'success': False, 'message': '存在进行中的任务，车辆不能设为可用'}), 400

        vehicle.status = status
        db.session.commit()
        return jsonify({'success': True, 'data': vehicle.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


def bind_vehicle_by_plate():
    try:
        driver, _current_user_id = _get_current_driver_user()
        if not driver:
            return jsonify({'success': False, 'message': '当前账号不是司机账号'}), 404

        active_dispatch = Dispatch.query.filter(
            Dispatch.driver_id == driver.id,
            Dispatch.status.in_(['scheduled', 'in_progress'])
        ).first()
        if active_dispatch:
            return jsonify({'success': False, 'message': '当前有进行中的任务，不能更换绑定车辆'}), 400

        data = request.json or {}
        plate_number = data.get('plate_number')
        if not plate_number:
            return jsonify({'success': False, 'message': '请提供车牌号'}), 400

        vehicle = Vehicle.query.filter_by(plate_number=plate_number, is_deleted=False).first()
        if not vehicle:
            return jsonify({'success': False, 'message': '车牌号不存在'}), 404

        other_driver = User.query.filter(
            User.role == RoleEnum.driver,
            User.vehicle_id == vehicle.id,
            User.id != driver.id,
            User.is_deleted == False
        ).first()
        if other_driver:
            return jsonify({'success': False, 'message': '该车辆已绑定其他司机'}), 400

        driver.vehicle_id = vehicle.id
        db.session.commit()
        return jsonify({'success': True, 'data': {'driver_id': driver.id, 'vehicle_id': driver.vehicle_id, 'plate_number': vehicle.plate_number}})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
