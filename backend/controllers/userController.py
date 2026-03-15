# 用户管理控制器
from flask import request, jsonify
from models.index import db, User, Department


# 获取所有用户
def get_users():
    try:
        users = User.query.all()
        return jsonify({'success': True, 'data': [user.to_dict() for user in users]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 获取单个用户
def get_user(id):
    try:
        user = User.query.get(id)
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'})
        return jsonify({'success': True, 'data': user.to_dict()})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 创建用户
def create_user():
    try:
        data = request.json
        user = User(
            username=data['username'],
            password=data['password'],
            name=data['name'],
            email=data['email'],
            phone=data['phone'],
            department_id=data['department_id'],
            role=data['role']
        )
        db.session.add(user)
        db.session.commit()
        return jsonify({'success': True, 'data': user.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


# 更新用户
def update_user(id):
    try:
        user = User.query.get(id)
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'})
        
        data = request.json
        user.name = data.get('name', user.name)
        user.email = data.get('email', user.email)
        user.phone = data.get('phone', user.phone)
        user.department_id = data.get('department_id', user.department_id)
        user.role = data.get('role', user.role)
        
        db.session.commit()
        return jsonify({'success': True, 'data': user.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


# 删除用户
def delete_user(id):
    try:
        user = User.query.get(id)
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'})
        
        db.session.delete(user)
        db.session.commit()
        return jsonify({'success': True, 'message': '用户删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


# 部门管理接口
def get_departments():
    try:
        departments = Department.query.all()
        return jsonify({'success': True, 'data': [dept.to_dict() for dept in departments]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


def create_department():
    try:
        data = request.json
        department = Department(
            name=data['name'],
            leader_id=data['leader_id']
        )
        db.session.add(department)
        db.session.commit()
        return jsonify({'success': True, 'data': department.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})