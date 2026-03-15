# 用户相关路由
from flask import Blueprint, request, jsonify
from controllers.userController import get_users, get_user, create_user, update_user, delete_user, get_departments, create_department

userBlueprint = Blueprint('user', __name__, url_prefix='/api/users')

# 注册路由
userBlueprint.route('', methods=['GET'])(get_users)
userBlueprint.route('/<int:id>', methods=['GET'])(get_user)
userBlueprint.route('', methods=['POST'])(create_user)
userBlueprint.route('/<int:id>', methods=['PUT'])(update_user)
userBlueprint.route('/<int:id>', methods=['DELETE'])(delete_user)
userBlueprint.route('/departments', methods=['GET'])(get_departments)
userBlueprint.route('/departments', methods=['POST'])(create_department)