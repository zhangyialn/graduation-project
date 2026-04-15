"""司机自助操作领域服务。"""

from models.index import Dispatch, Vehicle, User, RoleEnum
from controllers.commonHelpers import enum_value


class DriverSelfServiceError(Exception):
    """司机自助操作业务异常。"""

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _get_active_dispatch(driver_id):
    return Dispatch.query.filter(
        Dispatch.driver_id == driver_id,
        Dispatch.status.in_(['scheduled', 'in_progress'])
    ).first()


def update_driver_status(driver, status):
    if status not in ['available', 'unavailable']:
        raise DriverSelfServiceError('司机状态仅支持 available/unavailable', 400)

    active_dispatch = _get_active_dispatch(driver.id)
    if active_dispatch and status != enum_value(driver.driver_status):
        raise DriverSelfServiceError('司机已被调度，结束行程前不能修改状态', 400)

    if status == 'available' and active_dispatch:
        raise DriverSelfServiceError('司机存在进行中的任务，不能设为可用', 400)

    driver.driver_status = status
    return driver


def update_vehicle_status(driver, status):
    if status not in ['available', 'maintenance', 'unavailable']:
        raise DriverSelfServiceError('车辆状态仅支持 available/maintenance/unavailable', 400)

    vehicle = Vehicle.query.get(driver.vehicle_id)
    if not vehicle or vehicle.is_deleted:
        raise DriverSelfServiceError('绑定车辆不存在', 404)

    active_dispatch = _get_active_dispatch(driver.id)
    if active_dispatch and status != enum_value(vehicle.status):
        raise DriverSelfServiceError('司机已被调度，结束行程前不能修改车辆状态', 400)

    if status == 'available' and active_dispatch:
        raise DriverSelfServiceError('存在进行中的任务，车辆不能设为可用', 400)

    vehicle.status = status
    return vehicle


def bind_vehicle_by_plate(driver, plate_number):
    active_dispatch = _get_active_dispatch(driver.id)
    if active_dispatch:
        raise DriverSelfServiceError('当前有进行中的任务，不能更换绑定车辆', 400)

    if not plate_number:
        raise DriverSelfServiceError('请提供车牌号', 400)

    vehicle = Vehicle.query.filter_by(plate_number=plate_number, is_deleted=False).first()
    if not vehicle:
        raise DriverSelfServiceError('车牌号不存在', 404)

    other_driver = User.query.filter(
        User.role == RoleEnum.driver,
        User.vehicle_id == vehicle.id,
        User.id != driver.id,
        User.is_deleted == False
    ).first()
    if other_driver:
        raise DriverSelfServiceError('该车辆已绑定其他司机', 400)

    driver.vehicle_id = vehicle.id
    return vehicle
