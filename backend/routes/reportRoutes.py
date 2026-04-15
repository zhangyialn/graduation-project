"""统计报表相关路由定义。"""

# 报表相关路由
from flask import Blueprint
from controllers.reportController import get_department_usage, get_department_expenses, get_vehicle_usage, get_monthly_stats, get_driver_workload, get_user_application_stats
from middleware.authMiddleware import jwt_required

reportBlueprint = Blueprint('report', __name__, url_prefix='/api/reports')

# 注册路由
reportBlueprint.route('/department-usage', methods=['GET'])(jwt_required()(get_department_usage))
reportBlueprint.route('/department-expenses', methods=['GET'])(jwt_required()(get_department_expenses))
reportBlueprint.route('/vehicle-usage', methods=['GET'])(jwt_required()(get_vehicle_usage))
reportBlueprint.route('/monthly-stats', methods=['GET'])(jwt_required()(get_monthly_stats))
reportBlueprint.route('/driver-workload', methods=['GET'])(jwt_required()(get_driver_workload))
reportBlueprint.route('/user-application-stats', methods=['GET'])(jwt_required()(get_user_application_stats))
