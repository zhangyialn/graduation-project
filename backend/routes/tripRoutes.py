# 出车记录相关路由
from flask import Blueprint
from controllers.tripController import get_trips, get_trip, create_trip, end_trip, get_trip_expense, update_trip_expense, get_fuel_prices, create_fuel_price
from middleware.auth_middleware import jwt_required

tripBlueprint = Blueprint('trip', __name__, url_prefix='/api/trips')

# 注册路由
tripBlueprint.route('', methods=['GET'])(jwt_required()(get_trips))
tripBlueprint.route('/<int:id>', methods=['GET'])(jwt_required()(get_trip))
tripBlueprint.route('', methods=['POST'])(jwt_required()(create_trip))
tripBlueprint.route('/<int:id>/end', methods=['POST'])(jwt_required()(end_trip))
tripBlueprint.route('/<int:id>/expense', methods=['GET'])(jwt_required()(get_trip_expense))
tripBlueprint.route('/<int:id>/expense', methods=['PUT'])(jwt_required()(update_trip_expense))
tripBlueprint.route('/fuel-prices', methods=['GET'])(jwt_required()(get_fuel_prices))
tripBlueprint.route('/fuel-prices', methods=['POST'])(jwt_required()(create_fuel_price))