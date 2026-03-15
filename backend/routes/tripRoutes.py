# 出车记录相关路由
from flask import Blueprint
from controllers.tripController import get_trips, get_trip, create_trip, end_trip, get_trip_expense, update_trip_expense, get_fuel_prices, create_fuel_price

tripBlueprint = Blueprint('trip', __name__, url_prefix='/api/trips')

# 注册路由
tripBlueprint.route('', methods=['GET'])(get_trips)
tripBlueprint.route('/<int:id>', methods=['GET'])(get_trip)
tripBlueprint.route('', methods=['POST'])(create_trip)
tripBlueprint.route('/<int:id>/end', methods=['POST'])(end_trip)
tripBlueprint.route('/<int:id>/expense', methods=['GET'])(get_trip_expense)
tripBlueprint.route('/<int:id>/expense', methods=['PUT'])(update_trip_expense)
tripBlueprint.route('/fuel-prices', methods=['GET'])(get_fuel_prices)
tripBlueprint.route('/fuel-prices', methods=['POST'])(create_fuel_price)