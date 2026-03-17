# 参数验证中间件
from functools import wraps
from flask import request, jsonify
import re


def validate_request(required_fields=None, optional_fields=None):
    """参数验证装饰器
    
    Args:
        required_fields: 必填字段列表，如 ['username', 'password']
        optional_fields: 可选字段列表，如 ['email', 'phone']
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 获取请求数据
            data = request.get_json() or {}
            
            # 验证必填字段
            if required_fields:
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    return jsonify({
                        'success': False,
                        'message': f'缺少必填字段: {missing_fields}'
                    }), 400
            
            # 验证字段类型
            validation_errors = []
            
            # 验证邮箱格式
            if 'email' in data:
                email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
                if not re.match(email_pattern, data['email']):
                    validation_errors.append('邮箱格式不正确')
            
            # 验证手机号格式（中国手机号）
            if 'phone' in data:
                phone_pattern = r'^1[3-9]\d{9}$'
                if not re.match(phone_pattern, data['phone']):
                    validation_errors.append('手机号格式不正确')
            
            # 验证密码长度
            if 'password' in data:
                if len(data['password']) < 6:
                    validation_errors.append('密码长度至少6位')
            
            # 验证用户名长度
            if 'username' in data:
                if len(data['username']) < 3:
                    validation_errors.append('用户名长度至少3位')
            
            # 返回验证错误
            if validation_errors:
                return jsonify({
                    'success': False,
                    'message': '参数验证失败',
                    'errors': validation_errors
                }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def validate_id(id_param):
    """验证ID参数
    
    Args:
        id_param: ID参数
    
    Returns:
        bool: 是否有效
    """
    try:
        return isinstance(id_param, int) and id_param > 0
    except:
        return False