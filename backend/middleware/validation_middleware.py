"""请求参数校验中间件。

负责统一处理必填项、字段白名单和常见格式校验，并返回结构化错误信息。
"""

# 参数验证中间件
from functools import wraps
from flask import request, jsonify
import re


# 生成请求体验证装饰器：按接口声明规则做通用参数校验
def validate_request(required_fields=None, optional_fields=None):
    """参数验证装饰器
    
    Args:
        required_fields: 必填字段列表，如 ['username', 'password']
        optional_fields: 可选字段列表，如 ['email', 'phone']
    """
    # 返回真正作用于路由处理函数的装饰器
    def decorator(f):
        @wraps(f)
        # 执行请求前置校验，失败时直接返回 400
        def decorated_function(*args, **kwargs):
            if request.method in ['POST', 'PUT', 'PATCH'] and not request.is_json:
                return jsonify({
                    'success': False,
                    'message': '请求体必须为 JSON 格式'
                }), 400

            # 获取请求数据
            data = request.get_json() or {}
            if not isinstance(data, dict):
                return jsonify({
                    'success': False,
                    'message': '请求体必须是 JSON 对象'
                }), 400
            
            # 验证必填字段
            if required_fields:
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    errors = [{'field': field, 'message': '缺少必填字段'} for field in missing_fields]
                    return jsonify({
                        'success': False,
                        'message': f"缺少必填字段: {', '.join(missing_fields)}",
                        'errors': errors
                    }), 400

                empty_fields = [
                    field for field in required_fields
                    if field in data and (data[field] is None or (isinstance(data[field], str) and not data[field].strip()))
                ]
                if empty_fields:
                    errors = [{'field': field, 'message': '字段不能为空'} for field in empty_fields]
                    return jsonify({
                        'success': False,
                        'message': f"以下字段不能为空: {', '.join(empty_fields)}",
                        'errors': errors
                    }), 400

            # 限制允许字段（required + optional）
            if required_fields is not None or optional_fields is not None:
                allowed_fields = set(required_fields or []) | set(optional_fields or [])
                if allowed_fields:
                    unknown_fields = [field for field in data.keys() if field not in allowed_fields]
                    if unknown_fields:
                        errors = [{'field': field, 'message': '未允许字段'} for field in unknown_fields]
                        return jsonify({
                            'success': False,
                            'message': f"存在未允许字段: {', '.join(unknown_fields)}",
                            'errors': errors
                        }), 400
            
            # 验证字段类型
            validation_errors = []
            
            # 验证邮箱格式
            if 'email' in data:
                email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
                email_value = data.get('email')
                if email_value not in [None, '']:
                    if not isinstance(email_value, str) or not re.match(email_pattern, email_value):
                        validation_errors.append({'field': 'email', 'message': '邮箱格式不正确'})
            
            # 验证手机号格式（中国手机号）
            if 'phone' in data:
                phone_pattern = r'^1[3-9]\d{9}$'
                phone_value = data.get('phone')
                if phone_value not in [None, '']:
                    if not isinstance(phone_value, str) or not re.match(phone_pattern, phone_value):
                        validation_errors.append({'field': 'phone', 'message': '手机号格式不正确（需11位中国大陆手机号）'})
            
            # 验证密码长度
            if 'password' in data:
                password_value = data.get('password')
                if not isinstance(password_value, str):
                    validation_errors.append({'field': 'password', 'message': '密码必须为字符串'})
                elif len(password_value) < 6:
                    validation_errors.append({'field': 'password', 'message': '密码长度至少6位'})
            
            # 验证用户名长度
            if 'username' in data:
                username_value = data.get('username')
                if not isinstance(username_value, str):
                    validation_errors.append({'field': 'username', 'message': '用户名必须为字符串'})
                elif len(username_value) < 3:
                    validation_errors.append({'field': 'username', 'message': '用户名长度至少3位'})
            
            # 返回验证错误
            if validation_errors:
                detail = '；'.join([f"{item['field']}: {item['message']}" for item in validation_errors])
                return jsonify({
                    'success': False,
                    'message': f'参数验证失败：{detail}',
                    'errors': validation_errors
                }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# 校验 ID 是否为正整数
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
