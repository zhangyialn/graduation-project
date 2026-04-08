"""认证相关路由定义。"""

# 认证相关路由
from flask import Blueprint
from controllers.authController import register, login, refresh, get_current_user, change_password, update_account_settings, verify_phone, reset_password, bootstrap_admin, generate_bootstrap_key, get_bootstrap_status, get_dev_users, dev_switch_user
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
	validate_request(required_fields=['username', 'password'], username_min_length=None)(login)
)
authBlueprint.route('/refresh', methods=['POST'])(jwt_required()(refresh))
authBlueprint.route('/me', methods=['GET'])(jwt_required()(get_current_user))
authBlueprint.route('/change-password', methods=['POST'])(
	jwt_required()(
		validate_request(required_fields=['old_password', 'new_password'])(change_password)
	)
)
authBlueprint.route('/account-settings', methods=['POST'])(
	jwt_required()(
		validate_request(required_fields=['old_password'], optional_fields=['username', 'new_password'])(update_account_settings)
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

# 首个管理员初始化（仅系统无管理员时生效）
authBlueprint.route('/bootstrap-status', methods=['GET'])(get_bootstrap_status)
authBlueprint.route('/bootstrap-key', methods=['POST'])(generate_bootstrap_key)
authBlueprint.route('/bootstrap-admin', methods=['POST'])(bootstrap_admin)

# 开发模式角色切换
authBlueprint.route('/dev-users', methods=['GET'])(jwt_required()(get_dev_users))
authBlueprint.route('/dev-switch-user', methods=['POST'])(
	jwt_required()(
		validate_request(required_fields=['user_id'])(dev_switch_user)
	)
)
