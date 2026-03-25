"""全局异常处理与错误响应中间件。"""

# 错误处理中间件
from functools import wraps
from flask import jsonify
from werkzeug.exceptions import HTTPException
import logging


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
                'error': error_message
            }), 401

        @jwt_manager.invalid_token_loader
        # JWT 非法或签名不正确
        def jwt_invalid_token(error_message):
            return jsonify({
                'success': False,
                'message': '访问令牌无效',
                'error': error_message
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
            'message': error.description
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
