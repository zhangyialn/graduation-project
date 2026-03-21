# 用车申请相关路由
from flask import Blueprint
from controllers.applicationController import get_applications, get_application, create_application, update_application, cancel_application, get_my_applications, get_pending_applications
from middleware.auth_middleware import jwt_required

applicationBlueprint = Blueprint('application', __name__, url_prefix='/api/applications')

# 注册路由
applicationBlueprint.route('', methods=['GET'])(jwt_required()(get_applications))
applicationBlueprint.route('/<int:id>', methods=['GET'])(jwt_required()(get_application))
applicationBlueprint.route('', methods=['POST'])(jwt_required()(create_application))
applicationBlueprint.route('/<int:id>', methods=['PUT'])(jwt_required()(update_application))
applicationBlueprint.route('/<int:id>/cancel', methods=['POST'])(jwt_required()(cancel_application))
applicationBlueprint.route('/my/<int:user_id>', methods=['GET'])(jwt_required()(get_my_applications))
applicationBlueprint.route('/pending/<int:department_id>', methods=['GET'])(jwt_required()(get_pending_applications))