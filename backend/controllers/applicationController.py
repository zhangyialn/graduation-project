"""用车申请控制器。"""

# 用车申请控制器
from datetime import datetime
from flask import request, jsonify
from models.index import db, CarApplication, User, Vehicle, RoleEnum
from flask_jwt_extended import get_jwt_identity
from controllers.recommendation_utils import build_driver_recommendations
from controllers.common_helpers import enum_value as _enum_value, normalize_identity as _normalize_identity, parse_optional_pagination as _parse_optional_pagination, pagination_meta as _pagination_meta


LOCKED_APPLICATION_STATUSES = ['pending', 'approved', 'dispatched']


# 解析 ISO 时间字符串，兼容带 Z 后缀的 UTC 文本
def _parse_datetime(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).replace('Z', '+00:00')
    return datetime.fromisoformat(text)


# 判断司机是否已绑定到进行中的申请，避免重复占用
def _is_driver_locked(driver_id, exclude_application_id=None):
    query = CarApplication.query.filter(
        CarApplication.driver_id == driver_id,
        CarApplication.status.in_(LOCKED_APPLICATION_STATUSES)
    )
    if exclude_application_id:
        query = query.filter(CarApplication.id != exclude_application_id)
    return query.first() is not None


# 校验司机+车辆是否都可用，并且司机没有冲突申请
def _validate_driver_available(driver_id, exclude_application_id=None):
    driver = User.query.filter_by(id=driver_id, role=RoleEnum.driver, is_deleted=False).first()
    if not driver:
        return False, '司机不存在', None

    if _enum_value(driver.driver_status) != 'available':
        return False, '司机当前不可用', None

    vehicle = Vehicle.query.get(driver.vehicle_id)
    if not vehicle or vehicle.is_deleted:
        return False, '司机绑定车辆不存在', None

    if _enum_value(vehicle.status) != 'available':
        return False, '司机绑定车辆当前不可用', None

    if _is_driver_locked(driver_id, exclude_application_id=exclude_application_id):
        return False, '该司机已有进行中的申请，暂不可重复申请', None

    return True, '', driver


# 获取所有申请
# 查询申请列表（支持按状态筛选）
def get_applications():
    try:
        # 兼容老接口：未传 page/limit 时继续返回全量列表。
        page, limit, should_paginate = _parse_optional_pagination()
        # 支持按状态筛选
        status = request.args.get('status')
        query = CarApplication.query
        if status:
            query = query.filter(CarApplication.status == status)

        if not should_paginate:
            applications = query.all()
            return jsonify({'success': True, 'data': [app.to_dict() for app in applications]})

        # 新分页模式：按倒序返回，确保新申请优先显示。
        total = query.count()
        applications = query.order_by(CarApplication.id.desc()).offset((page - 1) * limit).limit(limit).all()
        return jsonify({
            'success': True,
            'data': [app.to_dict() for app in applications],
            'pagination': _pagination_meta(total, page, limit)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 获取单个申请
# 查询单条申请详情
def get_application(id):
    try:
        application = CarApplication.query.get(id)
        if not application:
            return jsonify({'success': False, 'message': '申请不存在'})
        return jsonify({'success': True, 'data': application.to_dict()})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 创建用车申请
# 创建用车申请并校验司机可用性
def create_application():
    try:
        data = request.json
        required_fields = ['applicant_id', 'driver_id', 'start_time', 'purpose', 'destination', 'passenger_count']
        missing = [field for field in required_fields if data.get(field) in [None, '']]
        if missing:
            return jsonify({'success': False, 'message': f'缺少必填字段: {", ".join(missing)}'}), 400

        applicant = User.query.filter_by(id=int(data['applicant_id']), is_deleted=False).first()
        if not applicant:
            return jsonify({'success': False, 'message': '申请人不存在'}), 404
        if applicant.department_id in [None, 0]:
            return jsonify({'success': False, 'message': '申请人未配置所属部门，无法提交申请'}), 400

        request_department_id = data.get('department_id')
        if request_department_id not in [None, ''] and int(request_department_id) != int(applicant.department_id):
            return jsonify({'success': False, 'message': '部门必须与申请人所属部门一致'}), 400

        ok, message, _driver = _validate_driver_available(int(data['driver_id']))
        if not ok:
            return jsonify({'success': False, 'message': message}), 400

        start_time = _parse_datetime(data['start_time'])
        end_time = _parse_datetime(data.get('end_time')) or start_time

        application = CarApplication(
            applicant_id=int(data['applicant_id']),
            department_id=int(applicant.department_id),
            driver_id=int(data['driver_id']),
            start_point=data.get('start_point'),
            start_time=start_time,
            end_time=end_time,
            purpose=data['purpose'],
            destination=data['destination'],
            passenger_count=int(data['passenger_count']),
            expected_distance_km=data.get('expected_distance_km')
        )

        if application.start_time and application.end_time and application.end_time < application.start_time:
            return jsonify({'success': False, 'message': '结束时间不能早于开始时间'}), 400

        db.session.add(application)
        db.session.commit()
        return jsonify({'success': True, 'data': application.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


# 更新申请
# 更新申请（仅待审批状态允许修改）
def update_application(id):
    try:
        application = CarApplication.query.get(id)
        if not application:
            return jsonify({'success': False, 'message': '申请不存在'})
        
        # 只有待审批状态的申请才能修改
        if _enum_value(application.status) != 'pending':
            return jsonify({'success': False, 'message': '只有待审批的申请才能修改'})
        
        data = request.json
        if data.get('driver_id') is not None:
            new_driver_id = int(data['driver_id'])
            ok, message, _driver = _validate_driver_available(new_driver_id, exclude_application_id=id)
            if not ok:
                return jsonify({'success': False, 'message': message}), 400
            application.driver_id = new_driver_id

        if data.get('start_time'):
            application.start_time = _parse_datetime(data.get('start_time'))
        if data.get('end_time'):
            application.end_time = _parse_datetime(data.get('end_time'))

        if application.start_time and application.end_time and application.end_time < application.start_time:
            return jsonify({'success': False, 'message': '结束时间不能早于开始时间'}), 400

        application.start_point = data.get('start_point', application.start_point)
        application.purpose = data.get('purpose', application.purpose)
        application.destination = data.get('destination', application.destination)
        application.passenger_count = data.get('passenger_count', application.passenger_count)
        
        db.session.commit()
        return jsonify({'success': True, 'data': application.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


# 取消申请
# 取消申请（仅 pending/approved 可取消）
def cancel_application(id):
    try:
        application = CarApplication.query.get(id)
        if not application:
            return jsonify({'success': False, 'message': '申请不存在'})
        
        # 只有待审批或已批准的申请才能取消
        if _enum_value(application.status) not in ['pending', 'approved']:
            return jsonify({'success': False, 'message': '当前状态无法取消'})
        
        application.status = 'cancelled'
        db.session.commit()
        return jsonify({'success': True, 'data': application.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


# 获取我的申请列表
# 查询当前用户发起的申请
def get_my_applications(user_id):
    try:
        page, limit, should_paginate = _parse_optional_pagination()
        query = CarApplication.query.filter_by(applicant_id=user_id)
        # 支持状态过滤，供首页统计卡片按 rejected 快速计数。
        status = request.args.get('status')
        if status:
            query = query.filter(CarApplication.status == status)

        if not should_paginate:
            applications = query.all()
            return jsonify({'success': True, 'data': [app.to_dict() for app in applications]})

        total = query.count()
        applications = query.order_by(CarApplication.id.desc()).offset((page - 1) * limit).limit(limit).all()
        return jsonify({
            'success': True,
            'data': [app.to_dict() for app in applications],
            'pagination': _pagination_meta(total, page, limit)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 获取待审批列表（不按部门过滤）
def get_pending_applications(department_id=None):
    try:
        page, limit, should_paginate = _parse_optional_pagination()
        current_user_id = _normalize_identity(get_jwt_identity())

        query = CarApplication.query.filter(CarApplication.status == 'pending')
        if current_user_id is not None:
            # 自己提交的申请不出现在待审批列表中，避免“自己审批自己”。
            query = query.filter(CarApplication.applicant_id != current_user_id)

        if should_paginate:
            # 审批页默认按最新申请展示，减少翻页后“看不到新单”的情况。
            total = query.count()
            applications = query.order_by(CarApplication.id.desc()).offset((page - 1) * limit).limit(limit).all()
        else:
            applications = query.all()

        applicant_ids = list({app.applicant_id for app in applications if app.applicant_id})
        users = User.query.filter(User.id.in_(applicant_ids)).all() if applicant_ids else []
        user_map = {user.id: user for user in users}

        result = []
        for app in applications:
            item = app.to_dict()
            applicant = user_map.get(app.applicant_id)
            item['applicant_name'] = applicant.name if applicant else None
            result.append(item)

        payload = {'success': True, 'data': result}
        if should_paginate:
            payload['pagination'] = _pagination_meta(total, page, limit)
        return jsonify(payload)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 司机推荐：供用户申请页按人数/目的地获取排序候选
def get_recommended_drivers():
    try:
        raw_passenger_count = request.args.get('passenger_count', default='1')
        try:
            passenger_count = int(float(raw_passenger_count))
        except Exception:
            passenger_count = 1
        passenger_count = max(1, passenger_count)
        destination = request.args.get('destination', type=str) or ''
        ranked = build_driver_recommendations(passenger_count=passenger_count, destination=destination)

        # 推荐结果与创建申请使用同一口径：仅返回当前可申请的司机。
        applyable_ranked = []
        for item in ranked:
            driver_id = item.get('driver_id')
            if driver_id in [None, '']:
                continue
            ok, _message, _driver = _validate_driver_available(int(driver_id))
            if ok:
                applyable_ranked.append(item)

        return jsonify({'success': True, 'data': applyable_ranked})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
