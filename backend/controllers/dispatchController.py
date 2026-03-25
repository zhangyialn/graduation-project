"""调度控制器。"""

# 调度管理控制器
from flask import request, jsonify
from models.index import db, Dispatch, Vehicle, User, CarApplication, RoleEnum, Trip
from flask_jwt_extended import jwt_required
from datetime import datetime


# 兼容 Enum/字符串状态读取
def _enum_value(value):
    return value.value if hasattr(value, 'value') else value


# 统计司机当前进行中的调度任务数
def _driver_active_dispatch_count(driver_id):
    return Dispatch.query.filter(
        Dispatch.driver_id == driver_id,
        Dispatch.status.in_(['scheduled', 'in_progress'])
    ).count()


# 生成推荐说明（座位匹配 + 当前任务负载）
def _build_recommend_reason(seat_count, passenger_count, active_count):
    reasons = []
    if seat_count >= passenger_count:
        reasons.append(f'座位数满足需求（{seat_count}座）')
    else:
        reasons.append(f'座位数不足（{seat_count}座）')

    if active_count == 0:
        reasons.append('司机当前无进行中任务')
    else:
        reasons.append(f'司机当前任务数：{active_count}')
    return reasons


# 获取所有调度
# 查询调度列表（可按状态筛选）
def get_dispatches():
    try:
        # 支持按状态筛选
        status = request.args.get('status')
        if status:
            dispatches = Dispatch.query.filter_by(status=status).all()
        else:
            dispatches = Dispatch.query.all()
        return jsonify({'success': True, 'data': [dispatch.to_dict() for dispatch in dispatches]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 获取单个调度
# 查询单条调度详情
def get_dispatch(id):
    try:
        dispatch = Dispatch.query.get(id)
        if not dispatch:
            return jsonify({'success': False, 'message': '调度不存在'})
        return jsonify({'success': True, 'data': dispatch.to_dict()})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 创建调度（分配车辆和司机）
# 创建调度：校验申请、司机、车辆和时段冲突
def create_dispatch():
    try:
        data = request.json
        
        # 检查申请是否存在且已批准
        application = CarApplication.query.get(data['application_id'])
        if not application:
            return jsonify({'success': False, 'message': '申请不存在'})
        if _enum_value(application.status) != 'approved':
            return jsonify({'success': False, 'message': '申请未批准，无法调度'})

        expected_driver_id = data.get('driver_id', application.driver_id)
        if application.driver_id and int(expected_driver_id) != int(application.driver_id):
            return jsonify({'success': False, 'message': '该申请已指定司机，不能更换'}), 400

        driver = User.query.filter_by(id=int(expected_driver_id), role=RoleEnum.driver, is_deleted=False).first()
        if not driver:
            return jsonify({'success': False, 'message': '司机不存在'})

        # 司机和车辆强绑定：优先取司机绑定车辆
        bound_vehicle_id = driver.vehicle_id
        vehicle_id = int(data.get('vehicle_id') or bound_vehicle_id)
        if vehicle_id != bound_vehicle_id:
            return jsonify({'success': False, 'message': '所选车辆与司机绑定车辆不一致'}), 400
        
        # 检查车辆是否可用
        vehicle = Vehicle.query.get(vehicle_id)
        if not vehicle:
            return jsonify({'success': False, 'message': '车辆不存在'})
        if _enum_value(vehicle.status) != 'available':
            return jsonify({'success': False, 'message': '车辆不可用'})

        if _enum_value(driver.driver_status) != 'available':
            return jsonify({'success': False, 'message': '司机不可用'})
        
        # 检查车辆时间冲突
        # 这里需要通过dispatch关联到application来检查时间冲突
        from sqlalchemy import and_
        
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
            return jsonify({'success': False, 'message': '车辆在该时间段已被占用'})
        
        # 检查司机时间冲突
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
            return jsonify({'success': False, 'message': '司机在该时间段已被占用'})
        
        # 创建调度
        dispatch = Dispatch(
            application_id=data['application_id'],
            vehicle_id=vehicle_id,
            driver_id=int(expected_driver_id),
            dispatcher_id=data['dispatcher_id']
        )
        db.session.add(dispatch)
        
        # 更新车辆状态为使用中
        vehicle.status = 'in_use'
        
        # 更新司机状态为忙碌
        driver.driver_status = 'busy'
        
        # 更新申请状态为已调度
        application.status = 'dispatched'
        
        db.session.commit()
        return jsonify({'success': True, 'data': dispatch.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


# 开始出车
# 将调度状态从 scheduled 推进到 in_progress
def start_dispatch(id):
    try:
        dispatch = Dispatch.query.get(id)
        if not dispatch:
            return jsonify({'success': False, 'message': '调度不存在'})
        
        if _enum_value(dispatch.status) != 'scheduled':
            return jsonify({'success': False, 'message': '调度状态不正确'})

        # 开始调度时自动创建行程记录（若不存在）
        trip = Trip.query.filter_by(dispatch_id=dispatch.id).first()
        if not trip:
            trip = Trip(
                dispatch_id=dispatch.id,
                passenger_picked_up=False,
                status='started'
            )
            db.session.add(trip)
        
        dispatch.status = 'in_progress'
        db.session.commit()
        return jsonify({'success': True, 'data': dispatch.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


# 取消调度
# 取消调度并回滚车辆/司机/申请状态
def cancel_dispatch(id):
    try:
        dispatch = Dispatch.query.get(id)
        if not dispatch:
            return jsonify({'success': False, 'message': '调度不存在'})
        
        if _enum_value(dispatch.status) not in ['scheduled', 'in_progress']:
            return jsonify({'success': False, 'message': '当前状态无法取消'})
        
        # 更新调度状态
        dispatch.status = 'cancelled'
        
        # 恢复车辆状态
        vehicle = Vehicle.query.get(dispatch.vehicle_id)
        if vehicle:
            vehicle.status = 'available'
        
        # 恢复司机状态
        driver = User.query.filter_by(id=dispatch.driver_id, role=RoleEnum.driver, is_deleted=False).first()
        if driver:
            driver.driver_status = 'available'
        
        # 恢复申请状态
        application = CarApplication.query.get(dispatch.application_id)
        if application and _enum_value(application.status) == 'dispatched':
            application.status = 'approved'
        
        db.session.commit()
        return jsonify({'success': True, 'message': '调度已取消'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


# 获取待调度列表（已批准但未调度的申请）
# 查询待调度申请（已批准但未调度）
def get_pending_dispatches():
    try:
        applications = CarApplication.query.filter_by(status='approved').all()
        return jsonify({'success': True, 'data': [app.to_dict() for app in applications]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 为申请推荐司机与车辆（按座位匹配和负载评分）
def recommend_dispatch(application_id):
    try:
        application = CarApplication.query.get(application_id)
        if not application:
            return jsonify({'success': False, 'message': '申请不存在'}), 404

        if _enum_value(application.status) != 'approved':
            return jsonify({'success': False, 'message': '仅已批准申请可推荐调度'}), 400

        candidates_query = User.query.filter_by(role=RoleEnum.driver, is_deleted=False, driver_status='available')
        if application.driver_id:
            candidates_query = candidates_query.filter_by(id=application.driver_id)
        candidates = candidates_query.all()

        ranked = []
        for driver in candidates:
            vehicle = Vehicle.query.get(driver.vehicle_id)
            if not vehicle or vehicle.is_deleted:
                continue
            if _enum_value(vehicle.status) != 'available':
                continue

            seat_count = int(vehicle.seat_count or 0)
            passenger_count = int(application.passenger_count or 0)
            if seat_count < passenger_count:
                continue

            active_count = _driver_active_dispatch_count(driver.id)
            seat_score = 1 / (1 + max(seat_count - passenger_count, 0))
            workload_score = 1 / (1 + active_count)
            final_score = seat_score * 0.65 + workload_score * 0.35

            ranked.append({
                'driver_id': driver.id,
                'driver_name': driver.name,
                'vehicle_id': vehicle.id,
                'plate_number': vehicle.plate_number,
                'seat_count': seat_count,
                'active_dispatch_count': active_count,
                'score': round(final_score, 4),
                'reasons': _build_recommend_reason(seat_count, passenger_count, active_count)
            })

        ranked.sort(key=lambda item: item['score'], reverse=True)
        best = ranked[0] if ranked else None

        return jsonify({
            'success': True,
            'data': {
                'application_id': application_id,
                'best': best,
                'candidates': ranked[:5]
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
