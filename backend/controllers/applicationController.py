# 用车申请控制器
from flask import request, jsonify
from models.index import db, CarApplication


# 获取所有申请
def get_applications():
    try:
        # 支持按状态筛选
        status = request.args.get('status')
        if status:
            applications = CarApplication.query.filter_by(status=status).all()
        else:
            applications = CarApplication.query.all()
        return jsonify({'success': True, 'data': [app.to_dict() for app in applications]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 获取单个申请
def get_application(id):
    try:
        application = CarApplication.query.get(id)
        if not application:
            return jsonify({'success': False, 'message': '申请不存在'})
        return jsonify({'success': True, 'data': application.to_dict()})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 创建用车申请
def create_application():
    try:
        data = request.json
        application = CarApplication(
            applicant_id=data['applicant_id'],
            department_id=data['department_id'],
            start_time=data['start_time'],
            end_time=data['end_time'],
            purpose=data['purpose'],
            destination=data['destination'],
            passenger_count=data['passenger_count']
        )
        db.session.add(application)
        db.session.commit()
        return jsonify({'success': True, 'data': application.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


# 更新申请
def update_application(id):
    try:
        application = CarApplication.query.get(id)
        if not application:
            return jsonify({'success': False, 'message': '申请不存在'})
        
        # 只有待审批状态的申请才能修改
        if application.status != 'pending':
            return jsonify({'success': False, 'message': '只有待审批的申请才能修改'})
        
        data = request.json
        application.start_time = data.get('start_time', application.start_time)
        application.end_time = data.get('end_time', application.end_time)
        application.purpose = data.get('purpose', application.purpose)
        application.destination = data.get('destination', application.destination)
        application.passenger_count = data.get('passenger_count', application.passenger_count)
        
        db.session.commit()
        return jsonify({'success': True, 'data': application.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


# 取消申请
def cancel_application(id):
    try:
        application = CarApplication.query.get(id)
        if not application:
            return jsonify({'success': False, 'message': '申请不存在'})
        
        # 只有待审批或已批准的申请才能取消
        if application.status not in ['pending', 'approved']:
            return jsonify({'success': False, 'message': '当前状态无法取消'})
        
        application.status = 'cancelled'
        db.session.commit()
        return jsonify({'success': True, 'data': application.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


# 获取我的申请列表
def get_my_applications(user_id):
    try:
        applications = CarApplication.query.filter_by(applicant_id=user_id).all()
        return jsonify({'success': True, 'data': [app.to_dict() for app in applications]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 获取待审批列表（部门领导使用）
def get_pending_applications(department_id):
    try:
        applications = CarApplication.query.filter_by(
            department_id=department_id,
            status='pending'
        ).all()
        return jsonify({'success': True, 'data': [app.to_dict() for app in applications]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})