"""用户与部门相关路由定义。"""

# 用户相关路由
from flask import Blueprint
from controllers.userController import get_users, get_user, create_user, update_user, delete_user, get_departments, create_department, update_department, import_users_excel, create_admin_user, get_admin_options, assign_department_leader
from middleware.auth_middleware import jwt_required, role_required

userBlueprint = Blueprint('user', __name__, url_prefix='/api/users')

# 注册路由
userBlueprint.route('', methods=['GET'])(jwt_required()(get_users))
userBlueprint.route('/<int:id>', methods=['GET'])(jwt_required()(get_user))
userBlueprint.route('', methods=['POST'])(role_required(['admin'])(create_user))
userBlueprint.route('/import', methods=['POST'])(role_required(['admin'])(import_users_excel))
userBlueprint.route('/admins', methods=['POST'])(role_required(['admin'])(create_admin_user))
userBlueprint.route('/<int:id>', methods=['PUT'])(role_required(['approver', 'admin'])(update_user))
userBlueprint.route('/<int:id>', methods=['DELETE'])(role_required(['approver', 'admin'])(delete_user))
userBlueprint.route('/departments', methods=['GET'])(jwt_required()(get_departments))
userBlueprint.route('/departments', methods=['POST'])(role_required(['admin'])(create_department))
userBlueprint.route('/departments/<int:department_id>', methods=['PUT'])(role_required(['admin'])(update_department))
userBlueprint.route('/departments/admin-options', methods=['GET'])(role_required(['admin'])(get_admin_options))
userBlueprint.route('/departments/<int:department_id>/leader', methods=['PUT'])(role_required(['admin'])(assign_department_leader))
