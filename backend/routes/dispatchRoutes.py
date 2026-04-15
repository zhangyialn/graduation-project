"""调度相关路由定义。"""

# 调度相关路由
from flask import Blueprint
from controllers.dispatchController import get_dispatches, create_dispatch, start_dispatch, cancel_dispatch
from middleware.auth_middleware import jwt_required

dispatchBlueprint = Blueprint('dispatch', __name__, url_prefix='/api/dispatches')

# 注册路由
dispatchBlueprint.route('', methods=['GET'])(jwt_required()(get_dispatches))
dispatchBlueprint.route('', methods=['POST'])(jwt_required()(create_dispatch))
dispatchBlueprint.route('/<int:id>/start', methods=['POST'])(jwt_required()(start_dispatch))
dispatchBlueprint.route('/<int:id>/cancel', methods=['POST'])(jwt_required()(cancel_dispatch))
