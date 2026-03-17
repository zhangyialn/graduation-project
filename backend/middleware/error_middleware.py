# 错误处理中间件
from flask import jsonify
from werkzeug.exceptions import HTTPException
from flask_jwt_extended import InvalidTokenError, NoAuthorizationError
import logging


# 通用错误处理装饰器
def error_handler(f):
    """错误处理装饰器"""
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
def register_error_handlers(app):
    """注册全局错误处理器"""
    
    # 404错误
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({
            'success': False,
            'message': '请求的资源不存在'
        }), 404
    
    # 405错误
    @app.errorhandler(405)
    def method_not_allowed_error(error):
        return jsonify({
            'success': False,
            'message': '请求方法不允许'
        }), 405
    
    # JWT错误
    @app.errorhandler(InvalidTokenError)
    def invalid_token_error(error):
        return jsonify({
            'success': False,
            'message': '无效的令牌'
        }), 401
    
    @app.errorhandler(NoAuthorizationError)
    def no_authorization_error(error):
        return jsonify({
            'success': False,
            'message': '缺少认证令牌'
        }), 401
    
    # 通用HTTP错误
    @app.errorhandler(HTTPException)
    def http_error(error):
        return jsonify({
            'success': False,
            'message': error.description
        }), error.code
    
    # 其他错误
    @app.errorhandler(Exception)
    def general_error(error):
        logging.error(f"未捕获的错误: {str(error)}")
        return jsonify({
            'success': False,
            'message': '服务器内部错误'
        }), 500