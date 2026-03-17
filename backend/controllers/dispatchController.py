# 调度管理控制器
from flask import request, jsonify
from models.index import db, Dispatch, Vehicle, Driver, CarApplication
from flask_jwt_extended import jwt_required


# 获取所有调度
@jwt_required()
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
@jwt_required()
def get_dispatch(id):
    try:
        dispatch = Dispatch.query.get(id)
        if not dispatch:
            return jsonify({'success': False, 'message': '调度不存在'})
        return jsonify({'success': True, 'data': dispatch.to_dict()})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 创建调度（分配车辆和司机）
@jwt_required()
def create_dispatch():
    try:
        data = request.json
        
        # 检查申请是否存在且已批准
        application = CarApplication.query.get(data['application_id'])
        if not application:
            return jsonify({'success': False, 'message': '申请不存在'})
        if application.status != 'approved':
            return jsonify({'success': False, 'message': '申请未批准，无法调度'})
        
        # 检查车辆是否可用
        vehicle = Vehicle.query.get(data['vehicle_id'])
        if not vehicle:
            return jsonify({'success': False, 'message': '车辆不存在'})
        if vehicle.status != 'available':
            return jsonify({'success': False, 'message': '车辆不可用'})
        
        # 检查司机是否可用
        driver = Driver.query.get(data['driver_id'])
        if not driver:
            return jsonify({'success': False, 'message': '司机不存在'})
        if driver.status != 'available':
            return jsonify({'success': False, 'message': '司机不可用'})
        
        # 检查车辆时间冲突
        # 这里需要通过dispatch关联到application来检查时间冲突
        from sqlalchemy import and_
        
        conflict_dispatch = db.session.query(Dispatch).join(
            CarApplication, Dispatch.application_id == CarApplication.id
        ).filter(
            Dispatch.vehicle_id == data['vehicle_id'],
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
            Dispatch.driver_id == data['driver_id'],
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
            vehicle_id=data['vehicle_id'],
            driver_id=data['driver_id'],
            dispatcher_id=data['dispatcher_id']
        )
        db.session.add(dispatch)
        
        # 更新车辆状态为使用中
        vehicle.status = 'in_use'
        
        # 更新司机状态为忙碌
        driver.status = 'busy'
        
        # 更新申请状态为已调度
        application.status = 'dispatched'
        
        db.session.commit()
        return jsonify({'success': True, 'data': dispatch.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


# 开始出车
@jwt_required()
def start_dispatch(id):
    try:
        dispatch = Dispatch.query.get(id)
        if not dispatch:
            return jsonify({'success': False, 'message': '调度不存在'})
        
        if dispatch.status != 'scheduled':
            return jsonify({'success': False, 'message': '调度状态不正确'})
        
        dispatch.status = 'in_progress'
        db.session.commit()
        return jsonify({'success': True, 'data': dispatch.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


# 取消调度
@jwt_required()
def cancel_dispatch(id):
    try:
        dispatch = Dispatch.query.get(id)
        if not dispatch:
            return jsonify({'success': False, 'message': '调度不存在'})
        
        if dispatch.status not in ['scheduled', 'in_progress']:
            return jsonify({'success': False, 'message': '当前状态无法取消'})
        
        # 更新调度状态
        dispatch.status = 'cancelled'
        
        # 恢复车辆状态
        vehicle = Vehicle.query.get(dispatch.vehicle_id)
        if vehicle:
            vehicle.status = 'available'
        
        # 恢复司机状态
        driver = Driver.query.get(dispatch.driver_id)
        if driver:
            driver.status = 'available'
        
        # 恢复申请状态
        application = CarApplication.query.get(dispatch.application_id)
        if application:
            application.status = 'approved'
        
        db.session.commit()
        return jsonify({'success': True, 'message': '调度已取消'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


# 获取待调度列表（已批准但未调度的申请）
@jwt_required()
def get_pending_dispatches():
    try:
        applications = CarApplication.query.filter_by(status='approved').all()
        return jsonify({'success': True, 'data': [app.to_dict() for app in applications]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})