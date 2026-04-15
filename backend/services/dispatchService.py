"""调度领域服务。"""

from sqlalchemy import and_
from models.index import db, Dispatch, Vehicle, User, CarApplication, RoleEnum, Trip
from controllers.commonHelpers import enum_value


class DispatchServiceError(Exception):
    """调度业务异常。"""

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def create_dispatch(data):
    """创建调度并联动更新车辆、司机、申请状态，不负责 commit/rollback。"""
    application = CarApplication.query.get(data['application_id'])
    if not application:
        raise DispatchServiceError('申请不存在', 404)
    if enum_value(application.status) != 'approved':
        raise DispatchServiceError('申请未批准，无法调度', 400)

    expected_driver_id = data.get('driver_id', application.driver_id)
    if application.driver_id and int(expected_driver_id) != int(application.driver_id):
        raise DispatchServiceError('该申请已指定司机，不能更换', 400)

    driver = User.query.filter_by(id=int(expected_driver_id), role=RoleEnum.driver, is_deleted=False).first()
    if not driver:
        raise DispatchServiceError('司机不存在', 404)

    bound_vehicle_id = driver.vehicle_id
    vehicle_id = int(data.get('vehicle_id') or bound_vehicle_id)
    if vehicle_id != bound_vehicle_id:
        raise DispatchServiceError('所选车辆与司机绑定车辆不一致', 400)

    vehicle = Vehicle.query.get(vehicle_id)
    if not vehicle:
        raise DispatchServiceError('车辆不存在', 404)
    if enum_value(vehicle.status) != 'available':
        raise DispatchServiceError('车辆不可用', 400)

    if enum_value(driver.driver_status) != 'available':
        raise DispatchServiceError('司机不可用', 400)

    conflict_dispatch = db.session.query(Dispatch).join(
        CarApplication, Dispatch.application_id == CarApplication.id
    ).filter(
        Dispatch.vehicle_id == vehicle_id,
        Dispatch.status.in_(['scheduled', 'in_progress']),
        and_(
            CarApplication.start_time <= application.end_time,
            CarApplication.end_time >= application.start_time
        )
    ).first()

    if conflict_dispatch:
        raise DispatchServiceError('车辆在该时间段已被占用', 400)

    conflict_driver_dispatch = db.session.query(Dispatch).join(
        CarApplication, Dispatch.application_id == CarApplication.id
    ).filter(
        Dispatch.driver_id == int(expected_driver_id),
        Dispatch.status.in_(['scheduled', 'in_progress']),
        and_(
            CarApplication.start_time <= application.end_time,
            CarApplication.end_time >= application.start_time
        )
    ).first()

    if conflict_driver_dispatch:
        raise DispatchServiceError('司机在该时间段已被占用', 400)

    dispatch = Dispatch(
        application_id=data['application_id'],
        vehicle_id=vehicle_id,
        driver_id=int(expected_driver_id),
        dispatcher_id=data['dispatcher_id']
    )
    db.session.add(dispatch)

    vehicle.status = 'in_use'
    driver.driver_status = 'busy'
    application.status = 'dispatched'
    return dispatch


def start_dispatch(dispatch_id):
    """将调度状态从 scheduled 推进到 in_progress，不负责 commit/rollback。"""
    dispatch = Dispatch.query.get(dispatch_id)
    if not dispatch:
        raise DispatchServiceError('调度不存在', 404)

    if enum_value(dispatch.status) != 'scheduled':
        raise DispatchServiceError('调度状态不正确', 400)

    trip = Trip.query.filter_by(dispatch_id=dispatch.id).first()
    if not trip:
        trip = Trip(
            dispatch_id=dispatch.id,
            passenger_picked_up=False,
            status='started'
        )
        db.session.add(trip)

    dispatch.status = 'in_progress'
    return dispatch


def cancel_dispatch(dispatch_id):
    """取消调度并回滚车辆、司机、申请状态，不负责 commit/rollback。"""
    dispatch = Dispatch.query.get(dispatch_id)
    if not dispatch:
        raise DispatchServiceError('调度不存在', 404)

    if enum_value(dispatch.status) != 'scheduled':
        raise DispatchServiceError('仅未开始的调度可取消', 400)

    trip = Trip.query.filter_by(dispatch_id=dispatch.id).first()
    if trip and (trip.passenger_picked_up or trip.actual_start_time is not None):
        raise DispatchServiceError('司机已接到乘客，不能取消调度', 400)

    dispatch.status = 'cancelled'

    vehicle = Vehicle.query.get(dispatch.vehicle_id)
    if vehicle:
        vehicle.status = 'available'

    driver = User.query.filter_by(id=dispatch.driver_id, role=RoleEnum.driver, is_deleted=False).first()
    if driver:
        driver.driver_status = 'available'

    application = CarApplication.query.get(dispatch.application_id)
    if application and enum_value(application.status) == 'dispatched':
        application.status = 'approved'

    return dispatch
