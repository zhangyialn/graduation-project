# 调度相关路由
from flask import Blueprint
from controllers.dispatchController import get_dispatches, get_dispatch, create_dispatch, start_dispatch, cancel_dispatch, get_pending_dispatches

dispatchBlueprint = Blueprint('dispatch', __name__, url_prefix='/api/dispatches')

# 注册路由
dispatchBlueprint.route('', methods=['GET'])(get_dispatches)
dispatchBlueprint.route('/<int:id>', methods=['GET'])(get_dispatch)
dispatchBlueprint.route('', methods=['POST'])(create_dispatch)
dispatchBlueprint.route('/<int:id>/start', methods=['POST'])(start_dispatch)
dispatchBlueprint.route('/<int:id>/cancel', methods=['POST'])(cancel_dispatch)
dispatchBlueprint.route('/pending', methods=['GET'])(get_pending_dispatches)