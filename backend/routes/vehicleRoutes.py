# 车辆相关路由
from flask import Blueprint
from controllers.vehicleController import get_vehicles, get_vehicle, create_vehicle, update_vehicle, delete_vehicle, get_available_vehicles, get_drivers, create_driver, update_driver, delete_driver, get_available_drivers

vehicleBlueprint = Blueprint('vehicle', __name__, url_prefix='/api/vehicles')

# 注册路由
vehicleBlueprint.route('', methods=['GET'])(get_vehicles)
vehicleBlueprint.route('/<int:id>', methods=['GET'])(get_vehicle)
vehicleBlueprint.route('', methods=['POST'])(create_vehicle)
vehicleBlueprint.route('/<int:id>', methods=['PUT'])(update_vehicle)
vehicleBlueprint.route('/<int:id>', methods=['DELETE'])(delete_vehicle)
vehicleBlueprint.route('/available', methods=['GET'])(get_available_vehicles)
vehicleBlueprint.route('/drivers', methods=['GET'])(get_drivers)
vehicleBlueprint.route('/drivers', methods=['POST'])(create_driver)
vehicleBlueprint.route('/drivers/<int:id>', methods=['PUT'])(update_driver)
vehicleBlueprint.route('/drivers/<int:id>', methods=['DELETE'])(delete_driver)
vehicleBlueprint.route('/drivers/available', methods=['GET'])(get_available_drivers)