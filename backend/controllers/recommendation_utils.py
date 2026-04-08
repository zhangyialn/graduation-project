"""司机推荐算法工具。"""

from math import log1p
from models.index import db, User, Vehicle, Dispatch, Trip, CarApplication, RoleEnum


def _enum_value(value):
    return value.value if hasattr(value, 'value') else value


def _driver_active_dispatch_count(driver_id):
    return Dispatch.query.filter(
        Dispatch.driver_id == driver_id,
        Dispatch.status.in_(['scheduled', 'in_progress'])
    ).count()


def _driver_rating_avg(driver_id):
    value = db.session.query(db.func.avg(Trip.user_rating)).join(
        Dispatch, Dispatch.id == Trip.dispatch_id
    ).filter(
        Dispatch.driver_id == driver_id,
        Trip.user_rating.isnot(None)
    ).scalar()
    return float(value) if value is not None else None


def _driver_total_mileage(driver_id):
    value = db.session.query(db.func.sum(Trip.distance_km)).join(
        Dispatch, Dispatch.id == Trip.dispatch_id
    ).filter(
        Dispatch.driver_id == driver_id,
        Trip.distance_km.isnot(None),
        Trip.status == 'completed'
    ).scalar()
    return float(value) if value is not None else 0.0


def _driver_destination_count(driver_id, destination):
    if not destination:
        return 0
    return db.session.query(Trip.id).join(
        Dispatch, Dispatch.id == Trip.dispatch_id
    ).join(
        CarApplication, CarApplication.id == Dispatch.application_id
    ).filter(
        Dispatch.driver_id == driver_id,
        Trip.status == 'completed',
        CarApplication.destination == destination
    ).count()


def _seat_match_score(seat_count, passenger_count):
    if seat_count < passenger_count:
        return 0.0
    extra = max(seat_count - passenger_count, 0)
    # 满载最优，冗余座位越多分数越低，但保留基础分
    return max(0.45, 1 - 0.08 * extra)


def _rating_score(avg_rating):
    if avg_rating is None:
        # 冷启动司机给中性偏保守分，避免新司机永远排不到前列
        return 0.62
    return min(max(avg_rating / 5.0, 0.0), 1.0)


def _mileage_score(total_mileage_km):
    if total_mileage_km <= 0:
        return 0.0
    # 经验值用对数增长，避免超高里程垄断
    return min(log1p(total_mileage_km) / log1p(5000), 1.0)


def _destination_score(destination_count):
    if destination_count <= 0:
        return 0.0
    return min(destination_count / 6.0, 1.0)


def build_driver_recommendations(passenger_count, destination=None, specific_driver_id=None):
    passenger_count = int(passenger_count or 1)
    destination = str(destination or '').strip()

    query = User.query.filter_by(role=RoleEnum.driver, is_deleted=False, driver_status='available')
    if specific_driver_id:
        query = query.filter_by(id=int(specific_driver_id))

    drivers = query.all()
    ranked = []

    for driver in drivers:
        vehicle = Vehicle.query.get(driver.vehicle_id) if driver.vehicle_id else None
        if not vehicle or vehicle.is_deleted:
            continue
        if _enum_value(vehicle.status) != 'available':
            continue

        seat_count = int(vehicle.seat_count or 0)
        if seat_count < passenger_count:
            continue

        active_count = _driver_active_dispatch_count(driver.id)
        avg_rating = _driver_rating_avg(driver.id)
        total_mileage = _driver_total_mileage(driver.id)
        destination_count = _driver_destination_count(driver.id, destination)

        rating_component = _rating_score(avg_rating)
        mileage_component = _mileage_score(total_mileage)
        seat_component = _seat_match_score(seat_count, passenger_count)
        destination_component = _destination_score(destination_count)

        final_norm = (
            0.40 * rating_component
            + 0.20 * mileage_component
            + 0.20 * seat_component
            + 0.20 * destination_component
        )
        recommendation_index = round(min(5.0, max(0.0, final_norm * 5.0)), 2)

        reasons = [
            f"评分因子：{(avg_rating if avg_rating is not None else 3.1):.2f}/5",
            f"经验里程：{total_mileage:.1f}km",
            f"座位匹配：{seat_count}座/{passenger_count}人",
            f"同目的地历史：{destination_count}次"
        ]

        ranked.append({
            'driver_id': driver.id,
            'driver_name': driver.name,
            'vehicle_id': vehicle.id,
            'plate_number': vehicle.plate_number,
            'seat_count': seat_count,
            'active_dispatch_count': active_count,
            'avg_rating': round(avg_rating, 2) if avg_rating is not None else None,
            'total_mileage_km': round(total_mileage, 2),
            'destination_match_count': destination_count,
            'recommendation_index': recommendation_index,
            'score': round(final_norm, 4),
            'reasons': reasons
        })

    ranked.sort(
        key=lambda item: (
            item['recommendation_index'],
            item['destination_match_count'],
            -(item['active_dispatch_count'])
        ),
        reverse=True
    )
    return ranked
