"""全局异常处理与错误响应中间件。"""

# 错误处理中间件
from functools import wraps
from flask import jsonify
from werkzeug.exceptions import HTTPException
import logging


def _translate_jwt_error_message(error_message):
    """将常见 JWT 英文错误翻译为中文。"""
    text = str(error_message or '').strip().lower()
    mapping = {
        'missing authorization header': '未提供认证信息',
        'invalid header string': '认证头格式无效',
        'token has expired': '访问令牌已过期',
        'signature verification failed': '访问令牌签名校验失败',
        'not enough segments': '访问令牌格式错误',
        'subject must be a string': '令牌主体字段格式错误'
    }
    for key, value in mapping.items():
        if key in text:
            return value
    return '认证失败，请重新登录'


def _http_status_message_zh(status_code):
    """HTTP 状态码中文文案。"""
    mapping = {
        400: '请求参数错误',
        401: '未授权访问',
        403: '禁止访问',
        404: '请求的资源不存在',
        405: '请求方法不允许',
        408: '请求超时',
        409: '请求冲突',
        413: '请求体过大',
        415: '不支持的媒体类型',
        429: '请求过于频繁，请稍后再试',
        500: '服务器内部错误',
        502: '网关错误',
        503: '服务暂不可用',
        504: '网关超时'
    }
    return mapping.get(int(status_code or 500), '请求处理失败')


# 通用错误处理装饰器
# 通用函数级错误捕获装饰器
def error_handler(f):
    """错误处理装饰器"""
    @wraps(f)
    # 捕获未处理异常并返回统一错误结构
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logging.error(f"错误: {str(e)}")
            return jsonify({
                'success': False,
                'message': '服务器内部错误',
                'error': str(e)
            }), 500
    return decorated_function


# 注册全局错误处理器
# 注册应用级全局错误处理器（含 JWT 错误）
def register_error_handlers(app):
    """注册全局错误处理器"""

    jwt_manager = app.extensions.get('flask-jwt-extended')
    if jwt_manager:
        @jwt_manager.unauthorized_loader
        # 未携带 JWT
        def jwt_missing_token(error_message):
            return jsonify({
                'success': False,
                'message': '未提供访问令牌',
                'error': _translate_jwt_error_message(error_message)
            }), 401

        @jwt_manager.invalid_token_loader
        # JWT 非法或签名不正确
        def jwt_invalid_token(error_message):
            return jsonify({
                'success': False,
                'message': '访问令牌无效',
                'error': _translate_jwt_error_message(error_message)
            }), 401

        @jwt_manager.expired_token_loader
        # JWT 已过期
        def jwt_expired_token(jwt_header, jwt_payload):
            return jsonify({
                'success': False,
                'message': '访问令牌已过期'
            }), 401
    
    # 404错误
    @app.errorhandler(404)
    # 404 资源不存在
    def not_found_error(error):
        return jsonify({
            'success': False,
            'message': '请求的资源不存在'
        }), 404
    
    # 405错误
    @app.errorhandler(405)
    # 405 请求方法不允许
    def method_not_allowed_error(error):
        return jsonify({
            'success': False,
            'message': '请求方法不允许'
        }), 405
    
    # JWT错误 - 使用通用异常处理
    
    # 通用HTTP错误
    @app.errorhandler(HTTPException)
    # 其他 HTTP 异常
    def http_error(error):
        return jsonify({
            'success': False,
            'message': _http_status_message_zh(error.code)
        }), error.code
    
    # 其他错误
    @app.errorhandler(Exception)
    # 兜底异常处理
    def general_error(error):
        logging.error(f"未捕获的错误: {str(error)}")
        return jsonify({
            'success': False,
            'message': '服务器内部错误'
        }), 500
