"""认证与鉴权中间件。"""

# 认证中间件
from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import jwt_required as jwt_required_extended, get_jwt_identity
from models.index import User


# 规范化 JWT identity（优先转 int）
def _normalize_identity(identity):
    if identity is None:
        return None
    try:
        return int(identity)
    except Exception:
        return identity


# JWT认证装饰器
# 统一 JWT 认证装饰器，兼容两种调用形式
def jwt_required(f=None):
    """JWT认证装饰器，兼容 jwt_required()(f) 与 @jwt_required 两种写法"""
    # 返回实际装饰器
    def decorator(func):
        @wraps(func)
        @jwt_required_extended()
        # 执行 JWT 校验后调用原函数
        def decorated_function(*args, **kwargs):
            return func(*args, **kwargs)
        return decorated_function

    if f is None:
        return decorator
    return decorator(f)


# 角色权限检查装饰器
# 角色鉴权装饰器
def role_required(required_roles):
    """角色权限检查装饰器
    
    Args:
        required_roles: 所需角色列表，如 ['admin', 'approver']
    """
    # 返回实际装饰器
    def decorator(f):
        @wraps(f)
        @jwt_required_extended()
        # 校验当前用户角色是否在允许列表内
        def decorated_function(*args, **kwargs):
            current_user_id = _normalize_identity(get_jwt_identity())
            user = User.query.get(current_user_id)
            
            if not user:
                return jsonify({'success': False, 'message': '用户不存在'}), 404

            allowed_roles = required_roles
            if isinstance(required_roles, str):
                allowed_roles = [required_roles]

            user_role = user.role.value if hasattr(user.role, 'value') else user.role
            allowed_role_values = [role.value if hasattr(role, 'value') else role for role in allowed_roles]

            if user_role not in allowed_role_values:
                return jsonify({'success': False, 'message': '权限不足'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# 获取当前用户
# 读取当前登录用户对象
def get_current_user():
    """获取当前登录用户"""
    current_user_id = _normalize_identity(get_jwt_identity())
    if current_user_id is None:
        return None
    return User.query.get(current_user_id)
