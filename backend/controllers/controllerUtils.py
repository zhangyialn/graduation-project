"""控制器层通用事务与异常处理工具。"""

from functools import wraps
from flask import jsonify
from models.index import db


def transactional_endpoint(*service_error_types):
    """为写接口提供统一事务提交与异常响应。

    约定 service 侧业务异常包含 message/status_code 字段。
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                response = func(*args, **kwargs)
                db.session.commit()
                return response
            except service_error_types as e:
                db.session.rollback()
                message = getattr(e, 'message', str(e))
                status_code = getattr(e, 'status_code', 400)
                return jsonify({'success': False, 'message': message}), status_code
            except Exception as e:
                db.session.rollback()
                return jsonify({'success': False, 'message': str(e)}), 500

        return wrapper

    return decorator
