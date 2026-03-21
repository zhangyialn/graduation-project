# 认证相关路由
from flask import Blueprint
from controllers.authController import register, login, refresh, get_current_user, change_password
from middleware.auth_middleware import jwt_required
from middleware.validation_middleware import validate_request

authBlueprint = Blueprint('auth', __name__, url_prefix='/api/auth')

# 注册路由
authBlueprint.route('/register', methods=['POST'])(
	validate_request(
		required_fields=['username', 'password', 'name', 'email', 'phone', 'department_id'],
		optional_fields=['role']
	)(register)
)
authBlueprint.route('/login', methods=['POST'])(
	validate_request(required_fields=['username', 'password'])(login)
)
authBlueprint.route('/refresh', methods=['POST'])(jwt_required()(refresh))
authBlueprint.route('/me', methods=['GET'])(jwt_required()(get_current_user))
authBlueprint.route('/change-password', methods=['POST'])(
	jwt_required()(
		validate_request(required_fields=['old_password', 'new_password'])(change_password)
	)
)