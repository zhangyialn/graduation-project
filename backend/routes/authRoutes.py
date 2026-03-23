# 认证相关路由
from flask import Blueprint
from controllers.authController import register, login, refresh, get_current_user, change_password, verify_phone, reset_password
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

# 手机找回密码：验证手机与用户名匹配
authBlueprint.route('/verify-phone', methods=['POST'])(
	validate_request(required_fields=['username', 'phone'])(verify_phone)
)

# 手机找回密码：重置密码
authBlueprint.route('/reset-password', methods=['POST'])(
	validate_request(required_fields=['username', 'phone', 'new_password'])(reset_password)
)