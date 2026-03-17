# 认证中间件
from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import jwt_required as jwt_required_extended, get_jwt_identity
from models.index import User


# JWT认证装饰器
def jwt_required(f):
    """JWT认证装饰器"""
    @wraps(f)
    @jwt_required_extended()
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function


# 角色权限检查装饰器
def role_required(required_roles):
    """角色权限检查装饰器
    
    Args:
        required_roles: 所需角色列表，如 ['admin', 'leader']
    """
    def decorator(f):
        @wraps(f)
        @jwt_required_extended()
        def decorated_function(*args, **kwargs):
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user:
                return jsonify({'success': False, 'message': '用户不存在'}), 404
            
            if user.role not in required_roles:
                return jsonify({'success': False, 'message': '权限不足'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# 获取当前用户
def get_current_user():
    """获取当前登录用户"""
    current_user_id = get_jwt_identity()
    return User.query.get(current_user_id)