"""用车申请领域服务。"""

from datetime import datetime
from models.index import CarApplication, User, Vehicle, RoleEnum
from controllers.commonHelpers import enum_value


LOCKED_APPLICATION_STATUSES = ['pending', 'approved', 'dispatched']


def parse_datetime(value):
    """解析 ISO 时间字符串，兼容带 Z 后缀的 UTC 文本。"""
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).replace('Z', '+00:00')
    return datetime.fromisoformat(text)


def is_driver_locked(driver_id, exclude_application_id=None):
    """判断司机是否已绑定到进行中的申请，避免重复占用。"""
    query = CarApplication.query.filter(
        CarApplication.driver_id == driver_id,
        CarApplication.status.in_(LOCKED_APPLICATION_STATUSES)
    )
    if exclude_application_id:
        query = query.filter(CarApplication.id != exclude_application_id)
    return query.first() is not None


def validate_driver_available(driver_id, exclude_application_id=None):
    """校验司机+车辆是否都可用，并且司机没有冲突申请。"""
    driver = User.query.filter_by(id=driver_id, role=RoleEnum.driver, is_deleted=False).first()
    if not driver:
        return False, '司机不存在', None

    if enum_value(driver.driver_status) != 'available':
        return False, '司机当前不可用', None

    vehicle = Vehicle.query.get(driver.vehicle_id)
    if not vehicle or vehicle.is_deleted:
        return False, '司机绑定车辆不存在', None

    if enum_value(vehicle.status) != 'available':
        return False, '司机绑定车辆当前不可用', None

    if is_driver_locked(driver_id, exclude_application_id=exclude_application_id):
        return False, '该司机已有进行中的申请，暂不可重复申请', None

    return True, '', driver
