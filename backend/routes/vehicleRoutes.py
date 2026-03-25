"""车辆与司机管理相关路由定义。"""

# 车辆相关路由
from flask import Blueprint
from controllers.vehicleController import get_vehicles, get_vehicle, create_vehicle, update_vehicle, delete_vehicle, get_available_vehicles, get_drivers, create_driver, update_driver, delete_driver, get_available_drivers
from middleware.auth_middleware import jwt_required, role_required

vehicleBlueprint = Blueprint('vehicle', __name__, url_prefix='/api/vehicles')

# 注册路由
vehicleBlueprint.route('', methods=['GET'])(jwt_required()(get_vehicles))
vehicleBlueprint.route('/<int:id>', methods=['GET'])(jwt_required()(get_vehicle))
vehicleBlueprint.route('', methods=['POST'])(role_required(['approver', 'admin'])(create_vehicle))
vehicleBlueprint.route('/<int:id>', methods=['PUT'])(role_required(['approver', 'admin'])(update_vehicle))
vehicleBlueprint.route('/<int:id>', methods=['DELETE'])(role_required(['approver', 'admin'])(delete_vehicle))
vehicleBlueprint.route('/available', methods=['GET'])(jwt_required()(get_available_vehicles))
vehicleBlueprint.route('/drivers', methods=['GET'])(jwt_required()(get_drivers))
vehicleBlueprint.route('/drivers', methods=['POST'])(role_required(['approver', 'admin'])(create_driver))
vehicleBlueprint.route('/drivers/<int:id>', methods=['PUT'])(role_required(['approver', 'admin'])(update_driver))
vehicleBlueprint.route('/drivers/<int:id>', methods=['DELETE'])(role_required(['approver', 'admin'])(delete_driver))
vehicleBlueprint.route('/drivers/available', methods=['GET'])(jwt_required()(get_available_drivers))
