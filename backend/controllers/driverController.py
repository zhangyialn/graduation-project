"""司机工作台控制器。"""

from flask import request, jsonify
from flask_jwt_extended import get_jwt_identity
from models.index import db, User, RoleEnum
from services.driverDashboardService import build_driver_dashboard
from services.driverSelfService import (
    update_driver_status as update_driver_status_service,
    update_vehicle_status as update_vehicle_status_service,
    bind_vehicle_by_plate as bind_vehicle_by_plate_service,
    DriverSelfServiceError,
)
from controllers.controllerUtils import transactional_endpoint


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


@transactional_endpoint(DriverSelfServiceError)
def update_my_status():
    driver, _current_user_id = _get_current_driver_user()
    if not driver:
        return jsonify({'success': False, 'message': '当前账号不是司机账号'}), 404

    data = request.json or {}
    status = data.get('status')
    driver = update_driver_status_service(driver, status)
    return jsonify({'success': True, 'data': driver.to_dict()})


@transactional_endpoint(DriverSelfServiceError)
def update_my_vehicle_status():
    driver, _current_user_id = _get_current_driver_user()
    if not driver:
        return jsonify({'success': False, 'message': '当前账号不是司机账号'}), 404

    data = request.json or {}
    status = data.get('status')
    vehicle = update_vehicle_status_service(driver, status)
    return jsonify({'success': True, 'data': vehicle.to_dict()})


@transactional_endpoint(DriverSelfServiceError)
def bind_vehicle_by_plate():
    driver, _current_user_id = _get_current_driver_user()
    if not driver:
        return jsonify({'success': False, 'message': '当前账号不是司机账号'}), 404

    data = request.json or {}
    plate_number = data.get('plate_number')
    vehicle = bind_vehicle_by_plate_service(driver, plate_number)
    return jsonify({'success': True, 'data': {'driver_id': driver.id, 'vehicle_id': driver.vehicle_id, 'plate_number': vehicle.plate_number}})
