"""出车与费用控制器。"""

# 出车记录和费用管理控制器
from flask import request, jsonify
from flask_jwt_extended import get_jwt_identity
from models.index import db, Trip, Expense, Dispatch, Vehicle, FuelPrice, CarApplication, User, RoleEnum


# 兼容 Enum/字符串状态读取
def _enum_value(value):
    return value.value if hasattr(value, 'value') else value


# 获取所有出车记录
# 查询出车记录列表
def get_trips():
    try:
        trips = Trip.query.all()
        return jsonify({'success': True, 'data': [trip.to_dict() for trip in trips]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 获取单个出车记录
# 查询单条出车记录
def get_trip(id):
    try:
        trip = Trip.query.get(id)
        if not trip:
            return jsonify({'success': False, 'message': '出车记录不存在'})
        return jsonify({'success': True, 'data': trip.to_dict()})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 创建出车记录
# 创建出车记录（绑定调度）
def create_trip():
    try:
        data = request.json
        
        # 检查调度是否存在
        dispatch = Dispatch.query.get(data['dispatch_id'])
        if not dispatch:
            return jsonify({'success': False, 'message': '调度不存在'})
        
        trip = Trip(
            dispatch_id=data['dispatch_id'],
            start_mileage=data['start_mileage'],
            start_fuel=data['start_fuel'],
            actual_start_time=data.get('actual_start_time')
        )
        db.session.add(trip)
        db.session.commit()
        return jsonify({'success': True, 'data': trip.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


# 结束出车（用户或司机填写油耗和里程）
# 结束行程并计算费用，同时回写车辆/司机/调度/申请状态
def end_trip(id):
    try:
        trip = Trip.query.get(id)
        if not trip:
            return jsonify({'success': False, 'message': '出车记录不存在'})
        
        if _enum_value(trip.status) == 'completed':
            return jsonify({'success': False, 'message': '该行程已结束'})

        data = request.json or {}

        dispatch = Dispatch.query.get(trip.dispatch_id)
        if not dispatch:
            return jsonify({'success': False, 'message': '调度不存在'}), 404

        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        if not current_user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404

        current_role = _enum_value(current_user.role)
        driver_profile = User.query.filter_by(id=current_user_id, role=RoleEnum.driver, is_deleted=False).first()

        if current_role == 'driver':
            if not driver_profile or driver_profile.id != dispatch.driver_id:
                return jsonify({'success': False, 'message': '仅该行程司机可结束当前行程'}), 403
        
        # 更新出车记录
        trip.end_mileage = data['end_mileage']
        trip.end_fuel = data['end_fuel']
        trip.actual_end_time = data.get('actual_end_time')
        trip.ended_by = current_user_id
        trip.status = 'completed'

        mileage = float(trip.end_mileage) - float(trip.start_mileage)
        if mileage < 0:
            return jsonify({'success': False, 'message': '结束里程不能小于起始里程'}), 400
        trip.distance_km = mileage
        
        if dispatch:
            # 更新车辆状态为可用
            vehicle = Vehicle.query.get(dispatch.vehicle_id)
            if vehicle and _enum_value(vehicle.status) == 'in_use':
                vehicle.status = 'available'
            
            # 更新司机状态为可用
            driver = User.query.filter_by(id=dispatch.driver_id, role=RoleEnum.driver, is_deleted=False).first()
            if driver and _enum_value(driver.driver_status) == 'busy':
                driver.driver_status = 'available'
            
            # 更新调度状态为已完成
            dispatch.status = 'completed'

            application = CarApplication.query.get(dispatch.application_id)
            if application:
                application.status = 'completed'
        
        # 计算费用（兼容精细油号：92/95/98号汽油、0号柴油）
        vehicle_fuel_type = vehicle.fuel_type if vehicle else '汽油'
        latest_price = FuelPrice.query.filter_by(
            fuel_type=vehicle_fuel_type
        ).order_by(FuelPrice.effective_date.desc()).first()

        if not latest_price:
            if vehicle_fuel_type in ['汽油', '92号汽油', '95号汽油', '98号汽油']:
                latest_price = FuelPrice.query.filter(
                    FuelPrice.fuel_type.in_(['汽油', '92号汽油', '95号汽油', '98号汽油'])
                ).order_by(FuelPrice.effective_date.desc()).first()
            elif vehicle_fuel_type in ['柴油', '0号柴油']:
                latest_price = FuelPrice.query.filter(
                    FuelPrice.fuel_type.in_(['柴油', '0号柴油'])
                ).order_by(FuelPrice.effective_date.desc()).first()

        request_fuel_price = data.get('fuel_price')
        fuel_price_value = float(request_fuel_price) if request_fuel_price is not None else float(latest_price.price) if latest_price else 0.0

        request_cost_per_km = data.get('cost_per_km')
        if request_cost_per_km is not None:
            cost_per_km = float(request_cost_per_km)
        elif vehicle and vehicle.fuel_consumption_per_100km is not None:
            cost_per_km = float(vehicle.fuel_consumption_per_100km) / 100 * fuel_price_value
        else:
            cost_per_km = 0.0

        fuel_cost = mileage * cost_per_km

        # 维护费用（可由前端传入，默认 0）
        maintenance_cost = float(data.get('maintenance_cost', 0))
        
        # 其他费用
        other_cost = float(data.get('other_cost', 0))
        
        # 总费用
        total_cost = fuel_cost + maintenance_cost + other_cost
        
        # 创建费用记录
        expense = Expense(
            trip_id=id,
            mileage_km=mileage,
            cost_per_km=cost_per_km,
            fuel_cost=fuel_cost,
            maintenance_cost=maintenance_cost,
            other_cost=other_cost,
            total_cost=total_cost,
            fuel_price=fuel_price_value
        )
        db.session.add(expense)
        
        db.session.commit()
        return jsonify({
            'success': True,
            'data': {
                'trip': trip.to_dict(),
                'expense': expense.to_dict()
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


# 获取费用详情
# 查询行程费用明细
def get_trip_expense(id):
    try:
        expense = Expense.query.filter_by(trip_id=id).first()
        if not expense:
            return jsonify({'success': False, 'message': '费用记录不存在'})
        return jsonify({'success': True, 'data': expense.to_dict()})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 更新费用（用于添加过路费等其他费用）
# 更新行程费用补充项（如维护费/其他费）
def update_trip_expense(id):
    try:
        expense = Expense.query.filter_by(trip_id=id).first()
        if not expense:
            return jsonify({'success': False, 'message': '费用记录不存在'})
        
        data = request.json
        expense.other_cost = data.get('other_cost', expense.other_cost)
        expense.maintenance_cost = data.get('maintenance_cost', expense.maintenance_cost)
        expense.total_cost = float(expense.fuel_cost) + float(expense.maintenance_cost) + float(expense.other_cost)
        
        db.session.commit()
        return jsonify({'success': True, 'data': expense.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


# ==================== 燃油价格管理 ====================

# 获取燃油价格列表
# 查询油价配置列表
def get_fuel_prices():
    try:
        prices = FuelPrice.query.all()
        return jsonify({'success': True, 'data': [price.to_dict() for price in prices]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 添加燃油价格
# 新增油价配置
def create_fuel_price():
    try:
        data = request.json
        price = FuelPrice(
            fuel_type=data['fuel_type'],
            price=data['price'],
            effective_date=data['effective_date']
        )
        db.session.add(price)
        db.session.commit()
        return jsonify({'success': True, 'data': price.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})
