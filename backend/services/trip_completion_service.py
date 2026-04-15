"""行程结束事务编排服务。"""

from datetime import datetime
from models.index import db, Dispatch, Vehicle, User, CarApplication, RoleEnum
from controllers.common_helpers import enum_value, normalize_identity
from services.trip_fuel_service import calculate_trip_expense, upsert_trip_expense


class TripCompletionError(Exception):
    """行程结束业务异常。"""

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _resolve_trip_input_data(trip, payload):
    distance_input = payload.get('distance_km')
    fuel_used_input = payload.get('fuel_used')

    if distance_input is None:
        distance_input = trip.driver_report_distance_km
    if fuel_used_input is None:
        fuel_used_input = trip.driver_report_fuel_used_l

    if distance_input is None:
        raise TripCompletionError('司机尚未填写里程，请先让司机填报', 400)

    mileage = float(distance_input)
    if mileage < 0:
        raise TripCompletionError('消耗路程不能为负数', 400)

    fuel_used_value = float(fuel_used_input) if fuel_used_input is not None else 0.0
    if fuel_used_value < 0:
        raise TripCompletionError('消耗油量不能为负数', 400)

    return mileage, fuel_used_value


def _validate_trip_completion_permission(trip, current_user_id):
    dispatch = Dispatch.query.get(trip.dispatch_id)
    if not dispatch:
        raise TripCompletionError('调度不存在', 404)

    application = CarApplication.query.get(dispatch.application_id)
    if not application:
        raise TripCompletionError('申请记录不存在', 404)

    if int(application.applicant_id) != int(normalize_identity(current_user_id)):
        raise TripCompletionError('仅乘客本人可结束行程', 403)

    return dispatch, application


def _sync_related_entity_states(dispatch, application):
    vehicle = Vehicle.query.get(dispatch.vehicle_id)
    if vehicle and enum_value(vehicle.status) == 'in_use':
        vehicle.status = 'available'

    driver = User.query.filter_by(id=dispatch.driver_id, role=RoleEnum.driver, is_deleted=False).first()
    if driver and enum_value(driver.driver_status) == 'busy':
        driver.driver_status = 'available'

    dispatch.status = 'completed'
    if application:
        application.status = 'completed'

    return vehicle


def complete_trip(trip, payload, current_user_id):
    """处理结束行程全流程，不负责 commit/rollback。"""
    if enum_value(trip.status) == 'completed':
        raise TripCompletionError('该行程已结束', 400)

    dispatch, application = _validate_trip_completion_permission(trip, current_user_id)

    picked_up = bool(trip.passenger_picked_up) or (trip.actual_start_time is not None)
    if not picked_up:
        raise TripCompletionError('请先确认已接到乘客，再结束行程', 400)
    if not trip.passenger_picked_up:
        trip.passenger_picked_up = True

    mileage, fuel_used_value = _resolve_trip_input_data(trip, payload)

    trip.actual_end_time = datetime.utcnow()
    trip.ended_by = normalize_identity(current_user_id)
    trip.status = 'completed'
    trip.distance_km = mileage
    trip.fuel_used_l = fuel_used_value

    vehicle = _sync_related_entity_states(dispatch, application)

    expense_calc = calculate_trip_expense(
        mileage=mileage,
        fuel_used_value=fuel_used_value,
        vehicle=vehicle,
        request_fuel_price=payload.get('fuel_price'),
        request_cost_per_km=payload.get('cost_per_km')
    )

    trip.total_cost = expense_calc['total_cost']

    expense = upsert_trip_expense(
        trip_id=trip.id,
        mileage=mileage,
        cost_per_km=expense_calc['cost_per_km'],
        fuel_cost=expense_calc['fuel_cost'],
        total_cost=expense_calc['total_cost'],
        fuel_price_value=expense_calc['fuel_price_value']
    )

    return {
        'trip': trip,
        'expense': expense
    }
