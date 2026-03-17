# 认证相关路由
from flask import Blueprint
from flask_jwt_extended import jwt_required
from controllers.authController import register, login, refresh, get_current_user, change_password

authBlueprint = Blueprint('auth', __name__, url_prefix='/api/auth')

# 注册路由
authBlueprint.route('/register', methods=['POST'])(register)
authBlueprint.route('/login', methods=['POST'])(login)
authBlueprint.route('/refresh', methods=['POST'])(jwt_required()(refresh))
authBlueprint.route('/me', methods=['GET'])(get_current_user)
authBlueprint.route('/change-password', methods=['POST'])(change_password)