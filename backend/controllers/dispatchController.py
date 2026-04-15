"""调度控制器。"""

# 调度管理控制器
from flask import request, jsonify
from models.index import db, Dispatch, Vehicle, User, CarApplication, RoleEnum, Trip
from controllers.common_helpers import enum_value as _enum_value


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
        
        if _enum_value(dispatch.status) != 'scheduled':
            return jsonify({'success': False, 'message': '仅未开始的调度可取消'})

        trip = Trip.query.filter_by(dispatch_id=dispatch.id).first()
        if trip and (trip.passenger_picked_up or trip.actual_start_time is not None):
            return jsonify({'success': False, 'message': '司机已接到乘客，不能取消调度'}), 400
        
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


