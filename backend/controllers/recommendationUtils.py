"""司机推荐算法工具。"""

from math import log1p
import re
from models.index import db, User, Vehicle, Dispatch, Trip, CarApplication, RoleEnum
from controllers.common_helpers import enum_value as _enum_value


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


def _normalize_destination_text(text):
    value = str(text or '').strip().lower()
    if not value:
        return ''
    value = re.sub(r'[\s\-_,，。；;、/\\()（）\[\]【】]+', '', value)
    # 弱化地名中常见泛化词，突出地点关键词
    for token in ['省', '市', '区', '县', '镇', '乡', '街道', '大道', '路', '号', '广场']:
        value = value.replace(token, '')
    return value


def _destination_similarity(a, b):
    text_a = _normalize_destination_text(a)
    text_b = _normalize_destination_text(b)
    if not text_a or not text_b:
        return 0.0
    if text_a == text_b:
        return 1.0

    set_a = set(text_a)
    set_b = set(text_b)
    char_jaccard = len(set_a & set_b) / max(1, len(set_a | set_b))

    # 2-gram 相似度，兼顾词序信息
    def _grams(text):
        if len(text) < 2:
            return {text}
        return {text[i:i + 2] for i in range(len(text) - 1)}

    grams_a = _grams(text_a)
    grams_b = _grams(text_b)
    gram_jaccard = len(grams_a & grams_b) / max(1, len(grams_a | grams_b))

    similarity = 0.55 * char_jaccard + 0.45 * gram_jaccard

    # 包含关系给额外提升（如“重庆北站”与“重庆北站南广场”）
    if text_a in text_b or text_b in text_a:
        short_len = min(len(text_a), len(text_b))
        long_len = max(len(text_a), len(text_b))
        contain_bonus = 0.78 + 0.22 * (short_len / max(1, long_len))
        similarity = max(similarity, contain_bonus)

    return min(max(similarity, 0.0), 1.0)


def _driver_destination_profile(driver_id, destination):
    target = _normalize_destination_text(destination)
    if not target:
        return {
            'best_similarity': 0.0,
            'strong_match_count': 0,
            'match_count': 0
        }

    rows = db.session.query(CarApplication.destination).select_from(Trip).join(
        Dispatch, Dispatch.id == Trip.dispatch_id
    ).join(
        CarApplication, CarApplication.id == Dispatch.application_id
    ).filter(
        Dispatch.driver_id == driver_id,
        Trip.status == 'completed'
    ).all()

    best_similarity = 0.0
    strong_match_count = 0
    match_count = 0

    for row in rows:
        candidate = row[0]
        similarity = _destination_similarity(target, candidate)
        if similarity >= 0.55:
            match_count += 1
        if similarity >= 0.72:
            strong_match_count += 1
        if similarity > best_similarity:
            best_similarity = similarity

    return {
        'best_similarity': round(best_similarity, 4),
        'strong_match_count': strong_match_count,
        'match_count': match_count
    }


def _seat_match_score(seat_count, passenger_count):
    if seat_count < passenger_count:
        return 0.0
    extra = max(seat_count - passenger_count, 0)
    # 新规则：在满足人数前提下，座位冗余越高评分越高（封顶 1.0）
    return min(1.0, 0.70 + 0.05 * extra)


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


def _destination_score(profile, destination_text):
    # 用户未输入目的地时，给中性分，避免无输入导致系统性降分
    if not str(destination_text or '').strip():
        return 0.60
    if not profile:
        return 0.0
    similarity = float(profile.get('best_similarity') or 0.0)
    strong_count = int(profile.get('strong_match_count') or 0)
    match_count = int(profile.get('match_count') or 0)

    strong_bonus = min(strong_count / 5.0, 1.0)
    match_bonus = min(match_count / 8.0, 1.0)

    # 目的地得分单调受匹配次数驱动：匹配次数越多，得分只增不减。
    score = 0.45 * similarity + 0.40 * strong_bonus + 0.15 * match_bonus

    # 只要命中同目的地历史，得分至少高于“未输入目的地”的中性分。
    if strong_count > 0:
        score = max(score, 0.68)
    elif match_count > 0:
        score = max(score, 0.62)

    return min(1.0, score)


def _workload_score(active_dispatch_count):
    # 任务越少越优，避免“忙司机”在同等条件下持续被推荐
    if active_dispatch_count <= 0:
        return 1.0
    return 1 / (1 + 0.6 * active_dispatch_count)


def build_driver_recommendations(passenger_count, destination=None, specific_driver_id=None):
    try:
        passenger_count = int(float(passenger_count or 1))
    except Exception:
        passenger_count = 1
    passenger_count = max(1, passenger_count)
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
        destination_profile = _driver_destination_profile(driver.id, destination)

        rating_component = _rating_score(avg_rating)
        mileage_component = _mileage_score(total_mileage)
        seat_component = _seat_match_score(seat_count, passenger_count)
        destination_component = _destination_score(destination_profile, destination)
        workload_component = _workload_score(active_count)

        final_norm = (
            0.33 * rating_component
            + 0.10 * mileage_component
            + 0.25 * seat_component
            + 0.22 * destination_component
            + 0.10 * workload_component
        )
        recommendation_index = round(min(5.0, max(0.0, final_norm * 5.0)), 2)

        reasons = [
            f"评分因子：{(avg_rating if avg_rating is not None else 3.1):.2f}/5",
            f"经验里程：{total_mileage:.1f}km",
            f"座位匹配：{seat_count}座/{passenger_count}人",
            f"目的地匹配度：{round(destination_profile.get('best_similarity', 0.0) * 100, 1)}%",
            f"同目的地历史：{destination_profile.get('strong_match_count', 0)}次",
            f"目的地因子：{round(destination_component * 5, 2)}/5",
            f"当前任务数：{active_count}"
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
            'destination_match_count': int(destination_profile.get('strong_match_count', 0)),
            'destination_match_similarity': float(destination_profile.get('best_similarity', 0.0)),
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
