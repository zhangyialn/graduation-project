"""司机工作台相关路由定义。"""

from flask import Blueprint
from controllers.driverController import get_my_dashboard, update_my_status, update_my_vehicle_status, bind_vehicle_by_plate
from middleware.authMiddleware import role_required


driverBlueprint = Blueprint('driver', __name__, url_prefix='/api/drivers')


driverBlueprint.route('/me/dashboard', methods=['GET'])(role_required(['driver', 'admin'])(get_my_dashboard))
driverBlueprint.route('/me/status', methods=['PUT'])(role_required(['driver', 'admin'])(update_my_status))
driverBlueprint.route('/me/vehicle-status', methods=['PUT'])(role_required(['driver', 'admin'])(update_my_vehicle_status))
driverBlueprint.route('/me/bind-vehicle', methods=['PUT'])(role_required(['driver', 'admin'])(bind_vehicle_by_plate))
