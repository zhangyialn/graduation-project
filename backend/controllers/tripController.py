"""出车与费用控制器。"""

# 出车记录和费用管理控制器
from flask import request, jsonify
from flask_jwt_extended import get_jwt_identity
from models.index import db, Trip, Expense, Dispatch, Vehicle, FuelPrice, CarApplication, User, RoleEnum
from datetime import datetime
import requests
from controllers.common_helpers import enum_value as _enum_value, normalize_identity as _normalize_identity, parse_optional_pagination as _parse_optional_pagination, pagination_meta as _pagination_meta
from services.trip_fuel_service import external_oil_cache, is_force_refresh, fetch_external_oil_prices, prepare_fuel_price_batch_items, upsert_fuel_prices_batch
from services.trip_completion_service import complete_trip, TripCompletionError
from controllers.controller_utils import transactional_endpoint

# 获取所有出车记录
# 查询出车记录列表
def get_trips():
    try:
        page, limit, should_paginate = _parse_optional_pagination()
        query = Trip.query

        if not should_paginate:
            trips = query.all()
            return jsonify({'success': True, 'data': [trip.to_dict() for trip in trips]})

        # 行程总览按 trip.id 倒序，确保最近行程优先可见。
        total = query.count()
        trips = query.order_by(Trip.id.desc()).offset((page - 1) * limit).limit(limit).all()
        return jsonify({
            'success': True,
            'data': [trip.to_dict() for trip in trips],
            'pagination': _pagination_meta(total, page, limit)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 行程管理列表（聚合乘客/司机/事由/费用）
def get_trip_management_list():
    try:
        page, limit, should_paginate = _parse_optional_pagination()
        query = Trip.query.order_by(Trip.created_at.desc(), Trip.id.desc())

        if should_paginate:
            # 管理页优先显示最新创建的行程。
            total = Trip.query.count()
            trips = query.offset((page - 1) * limit).limit(limit).all()
        else:
            trips = query.all()

        if not trips:
            payload = {'success': True, 'data': []}
            if should_paginate:
                payload['pagination'] = _pagination_meta(total, page, limit)
            return jsonify(payload)

        trip_ids = [trip.id for trip in trips]
        dispatch_ids = [trip.dispatch_id for trip in trips if trip.dispatch_id]

        dispatches = Dispatch.query.filter(Dispatch.id.in_(dispatch_ids)).all() if dispatch_ids else []
        dispatch_map = {item.id: item for item in dispatches}

        application_ids = [item.application_id for item in dispatches if item.application_id]
        applications = CarApplication.query.filter(CarApplication.id.in_(application_ids)).all() if application_ids else []
        application_map = {item.id: item for item in applications}

        user_ids = set()
        for item in applications:
            if item.applicant_id:
                user_ids.add(item.applicant_id)
        for item in dispatches:
            if item.driver_id:
                user_ids.add(item.driver_id)

        users = User.query.filter(User.id.in_(list(user_ids))).all() if user_ids else []
        user_map = {item.id: item for item in users}

        expenses = Expense.query.filter(Expense.trip_id.in_(trip_ids)).all() if trip_ids else []
        expense_map = {item.trip_id: item for item in expenses}

        result = []
        for trip in trips:
            dispatch = dispatch_map.get(trip.dispatch_id)
            application = application_map.get(dispatch.application_id) if dispatch else None
            passenger = user_map.get(application.applicant_id) if application and application.applicant_id else None
            driver = user_map.get(dispatch.driver_id) if dispatch and dispatch.driver_id else None
            expense = expense_map.get(trip.id)
            fuel_used_l = float(trip.fuel_used_l) if trip.fuel_used_l is not None else None

            distance_km = float(trip.distance_km) if trip.distance_km is not None else None
            if distance_km is None and expense and expense.mileage_km is not None:
                distance_km = float(expense.mileage_km)

            result.append({
                'trip_id': trip.id,
                'passenger_name': passenger.name if passenger else '未知乘客',
                'driver_name': driver.name if driver else '未知司机',
                'purpose': application.purpose if application else None,
                'distance_km': distance_km,
                'fuel_used_l': fuel_used_l,
                'total_cost': float(trip.total_cost) if trip.total_cost is not None else float(expense.total_cost) if expense and expense.total_cost is not None else 0.0,
                'user_rating': float(trip.user_rating) if trip.user_rating is not None else None,
                'passenger_picked_up': bool(trip.passenger_picked_up),
                'actual_start_time': trip.actual_start_time.isoformat() if trip.actual_start_time else None,
                'actual_end_time': trip.actual_end_time.isoformat() if trip.actual_end_time else None,
                'created_at': trip.created_at.isoformat() if trip.created_at else None
            })

        payload = {'success': True, 'data': result}
        if should_paginate:
            payload['pagination'] = _pagination_meta(total, page, limit)
        return jsonify(payload)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 司机确认“已接到乘客”并记录行程开始时间
def pickup_passenger(id):
    try:
        trip = Trip.query.get(id)
        if not trip:
            return jsonify({'success': False, 'message': '出车记录不存在'})

        if _enum_value(trip.status) == 'completed':
            return jsonify({'success': False, 'message': '该行程已结束，不能再接乘客'})

        dispatch = Dispatch.query.get(trip.dispatch_id)
        if not dispatch:
            return jsonify({'success': False, 'message': '调度不存在'}), 404

        current_user_id = _normalize_identity(get_jwt_identity())
        current_user = User.query.get(current_user_id)
        if not current_user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404

        current_role = _enum_value(current_user.role)
        driver_profile = User.query.filter_by(id=current_user_id, role=RoleEnum.driver, is_deleted=False).first()
        # 必须同时满足“司机角色 + 当前调度绑定司机”才能确认接客，防止越权操作。
        if current_role != 'driver' or not driver_profile or int(driver_profile.id) != int(dispatch.driver_id):
            return jsonify({'success': False, 'message': '仅该行程司机可确认接到乘客'}), 403

        if trip.passenger_picked_up or trip.actual_start_time is not None:
            if not trip.passenger_picked_up:
                trip.passenger_picked_up = True
                db.session.commit()
            return jsonify({'success': True, 'message': '已确认接到乘客', 'data': trip.to_dict()})

        trip.passenger_picked_up = True
        trip.actual_start_time = datetime.utcnow()
        db.session.commit()
        return jsonify({'success': True, 'message': '已确认接到乘客', 'data': trip.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


# 结束行程（仅乘客可结束），并按司机填报里程/油耗计算费用
@transactional_endpoint(TripCompletionError)
def end_trip(id):
    trip = Trip.query.get(id)
    if not trip:
        return jsonify({'success': False, 'message': '出车记录不存在'})
    data = request.json or {}
    current_user_id = _normalize_identity(get_jwt_identity())
    completion_result = complete_trip(trip, data, current_user_id)
    expense = completion_result['expense']

    return jsonify({
        'success': True,
        'data': {
            'trip': trip.to_dict(),
            'expense': expense.to_dict()
        }
    })


# 司机填写里程与油耗（不结束行程）
def submit_driver_trip_report(id):
    try:
        trip = Trip.query.get(id)
        if not trip:
            return jsonify({'success': False, 'message': '出车记录不存在'}), 404

        if _enum_value(trip.status) == 'completed':
            return jsonify({'success': False, 'message': '行程已结束，不能再填报'}), 400

        dispatch = Dispatch.query.get(trip.dispatch_id)
        if not dispatch:
            return jsonify({'success': False, 'message': '调度不存在'}), 404

        current_user_id = _normalize_identity(get_jwt_identity())
        driver = User.query.filter_by(id=current_user_id, role=RoleEnum.driver, is_deleted=False).first()
        if not driver or int(driver.id) != int(dispatch.driver_id):
            return jsonify({'success': False, 'message': '仅该行程司机可填报里程和油耗'}), 403

        data = request.json or {}
        distance_km = data.get('distance_km')
        fuel_used = data.get('fuel_used')
        if distance_km is None or fuel_used is None:
            return jsonify({'success': False, 'message': 'distance_km 和 fuel_used 必填'}), 400

        distance_km = float(distance_km)
        fuel_used = float(fuel_used)
        if distance_km < 0 or fuel_used < 0:
            return jsonify({'success': False, 'message': '里程和油耗不能为负数'}), 400

        trip.driver_report_distance_km = distance_km
        trip.driver_report_fuel_used_l = fuel_used
        trip.driver_reported_at = datetime.utcnow()
        db.session.commit()

        return jsonify({'success': True, 'message': '司机填报成功', 'data': trip.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# 用户对司机评分（满分5分）
def rate_trip(id):
    try:
        trip = Trip.query.get(id)
        if not trip:
            return jsonify({'success': False, 'message': '行程不存在'}), 404

        if _enum_value(trip.status) != 'completed':
            return jsonify({'success': False, 'message': '仅已完成行程可评分'}), 400

        dispatch = Dispatch.query.get(trip.dispatch_id)
        if not dispatch:
            return jsonify({'success': False, 'message': '调度不存在'}), 404
        application = CarApplication.query.get(dispatch.application_id)
        if not application:
            return jsonify({'success': False, 'message': '申请不存在'}), 404

        current_user_id = _normalize_identity(get_jwt_identity())
        if int(application.applicant_id) != int(current_user_id):
            return jsonify({'success': False, 'message': '仅乘客本人可评分'}), 403

        if trip.user_rating is not None:
            return jsonify({'success': False, 'message': '该行程已评分'}), 400

        data = request.json or {}
        rating = data.get('rating')
        if rating is None:
            return jsonify({'success': False, 'message': 'rating 为必填'}), 400

        rating = round(float(rating), 2)
        if rating < 0 or rating > 5:
            return jsonify({'success': False, 'message': '评分范围必须在 0 到 5 之间'}), 400

        trip.user_rating = rating
        trip.user_rated_by = current_user_id
        trip.user_rated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({'success': True, 'message': '评分成功', 'data': trip.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# 当前登录用户查看自己的行程
def get_my_trips():
    try:
        page, limit, should_paginate = _parse_optional_pagination()
        current_user_id = _normalize_identity(get_jwt_identity())
        current_user = User.query.get(current_user_id)
        if not current_user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404

        role_value = _enum_value(current_user.role)
        if role_value not in ['user', 'admin']:
            return jsonify({'success': False, 'message': '仅普通用户可查看我的行程'}), 403

        applications = CarApplication.query.filter_by(applicant_id=current_user_id).all()
        if not applications:
            return jsonify({'success': True, 'data': []})

        application_map = {item.id: item for item in applications}
        application_ids = list(application_map.keys())
        dispatches = Dispatch.query.filter(Dispatch.application_id.in_(application_ids)).all()
        dispatch_map = {item.application_id: item for item in dispatches}
        driver_ids = list({item.driver_id for item in dispatches if item.driver_id})
        drivers = User.query.filter(User.id.in_(driver_ids)).all() if driver_ids else []
        driver_map = {item.id: item for item in drivers}

        dispatch_ids = [item.id for item in dispatches]
        trips = Trip.query.filter(Trip.dispatch_id.in_(dispatch_ids)).all() if dispatch_ids else []
        trip_map = {item.dispatch_id: item for item in trips}

        rows = []
        for application in applications:
            dispatch = dispatch_map.get(application.id)
            trip = trip_map.get(dispatch.id) if dispatch else None
            driver = driver_map.get(dispatch.driver_id) if dispatch else None

            trip_status = _enum_value(trip.status) if trip else None
            can_end_by_user = bool(
                trip
                and trip_status != 'completed'
                and (trip.passenger_picked_up or trip.actual_start_time is not None)
            )
            can_rate = bool(trip and trip_status == 'completed' and trip.user_rating is None)

            rows.append({
                'application_id': application.id,
                'purpose': application.purpose,
                'destination': application.destination,
                'start_point': application.start_point,
                'start_time': application.start_time.isoformat() if application.start_time else None,
                'application_status': _enum_value(application.status),
                'dispatch_id': dispatch.id if dispatch else None,
                'dispatch_status': _enum_value(dispatch.status) if dispatch else None,
                'trip_id': trip.id if trip else None,
                'trip_status': trip_status,
                'passenger_picked_up': bool(trip.passenger_picked_up) if trip else False,
                'actual_start_time': trip.actual_start_time.isoformat() if trip and trip.actual_start_time else None,
                'actual_end_time': trip.actual_end_time.isoformat() if trip and trip.actual_end_time else None,
                'distance_km': float(trip.distance_km) if trip and trip.distance_km is not None else None,
                'fuel_used_l': float(trip.fuel_used_l) if trip and trip.fuel_used_l is not None else None,
                'total_cost': float(trip.total_cost) if trip and trip.total_cost is not None else None,
                'driver_name': driver.name if driver else None,
                'driver_id': driver.id if driver else None,
                'user_rating': float(trip.user_rating) if trip and trip.user_rating is not None else None,
                'can_end_by_user': can_end_by_user,
                'can_rate': can_rate
            })

        rows.sort(key=lambda item: item.get('application_id') or 0, reverse=True)

        if not should_paginate:
            return jsonify({'success': True, 'data': rows})

        # 当前接口先聚合后分页，total 以聚合后的可见行程数为准。
        total = len(rows)
        start = (page - 1) * limit
        end = start + limit
        return jsonify({
            'success': True,
            'data': rows[start:end],
            'pagination': _pagination_meta(total, page, limit)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== 燃油价格管理 ====================

# 代理第三方油价接口，避免前端浏览器直连触发 CORS 预检失败。
def get_external_oil_prices():
    try:
        now_ts = int(datetime.utcnow().timestamp())
        force_refresh = is_force_refresh(request.args.get('force'))

        # 命中短缓存直接返回，减少第三方接口整体耗时与失败概率。
        cached_payload = external_oil_cache.get_if_valid(now_ts, force_refresh=force_refresh)
        if cached_payload:
            return jsonify(cached_payload)

        raw_by_fuel = fetch_external_oil_prices()
        fetched_at = external_oil_cache.store(raw_by_fuel, now_ts)

        return jsonify({
            'success': True,
            'data': raw_by_fuel,
            'cached': False,
            'cached_at': fetched_at
        })
    except requests.exceptions.RequestException as e:
        return jsonify({'success': False, 'message': f'请求油价服务失败: {str(e)}'}), 502
    except ValueError:
        return jsonify({'success': False, 'message': '油价服务返回了无效JSON'}), 502
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# 获取燃油价格列表
# 查询油价配置列表
def get_fuel_prices():
    try:
        region_name = str(request.args.get('region_name') or '').strip()
        limit = request.args.get('limit', type=int)
        query = FuelPrice.query
        if region_name:
            query = query.filter(FuelPrice.region_name == region_name)
            query = query.order_by(
                FuelPrice.effective_date.desc(),
                FuelPrice.id.desc()
            )
        else:
            query = query.order_by(
                FuelPrice.effective_date.desc(),
                FuelPrice.region_name.asc(),
                FuelPrice.fuel_type.asc(),
                FuelPrice.id.desc()
            )

        if limit is not None:
            safe_limit = min(max(int(limit), 1), 2000)
            query = query.limit(safe_limit)

        prices = query.all()
        return jsonify({'success': True, 'data': [price.to_dict() for price in prices]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 批量新增/更新油价（按 region_name + fuel_type + effective_date 去重）。
def create_fuel_prices_batch():
    try:
        data = request.json or {}
        default_effective_date = data.get('effective_date')
        default_source = data.get('source')
        raw_items = data.get('items')

        if not isinstance(raw_items, list) or not raw_items:
            return jsonify({'success': False, 'message': 'items 必须是非空数组'}), 400
        if len(raw_items) > 1000:
            return jsonify({'success': False, 'message': '单次最多提交1000条油价记录'}), 400

        items = prepare_fuel_price_batch_items(
            raw_items,
            default_effective_date=default_effective_date,
            default_source=default_source
        )
        if items is None:
            return jsonify({'success': False, 'message': 'fuel_type、price、effective_date 必填'}), 400
        batch_result = upsert_fuel_prices_batch(items)

        db.session.commit()
        return jsonify({
            'success': True,
            'data': {
                'created': batch_result['created'],
                'updated': batch_result['updated'],
                'total': batch_result['total'],
                'sample': [row.to_dict() for row in batch_result['affected'][:5]]
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
