"""出车与费用控制器。"""

# 出车记录和费用管理控制器
from flask import request, jsonify
from flask_jwt_extended import get_jwt_identity
from models.index import db, Trip, Expense, Dispatch, Vehicle, FuelPrice, CarApplication, User, RoleEnum
from datetime import datetime


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


# 行程管理列表（聚合乘客/司机/事由/费用）
def get_trip_management_list():
    try:
        trips = Trip.query.order_by(Trip.created_at.desc(), Trip.id.desc()).all()
        if not trips:
            return jsonify({'success': True, 'data': []})

        trip_ids = [trip.id for trip in trips]
        dispatch_ids = [trip.dispatch_id for trip in trips if trip.dispatch_id]

        dispatches = Dispatch.query.filter(Dispatch.id.in_(dispatch_ids)).all() if dispatch_ids else []
        dispatch_map = {item.id: item for item in dispatches}

        application_ids = [item.application_id for item in dispatches if item.application_id]
        applications = CarApplication.query.filter(CarApplication.id.in_(application_ids)).all() if application_ids else []
        application_map = {item.id: item for item in applications}

        user_ids = set()
        for item in applications:
            if item.applicant_id:
                user_ids.add(item.applicant_id)
        for item in dispatches:
            if item.driver_id:
                user_ids.add(item.driver_id)

        users = User.query.filter(User.id.in_(list(user_ids))).all() if user_ids else []
        user_map = {item.id: item for item in users}

        expenses = Expense.query.filter(Expense.trip_id.in_(trip_ids)).all() if trip_ids else []
        expense_map = {item.trip_id: item for item in expenses}

        result = []
        for trip in trips:
            dispatch = dispatch_map.get(trip.dispatch_id)
            application = application_map.get(dispatch.application_id) if dispatch else None
            passenger = user_map.get(application.applicant_id) if application and application.applicant_id else None
            driver = user_map.get(dispatch.driver_id) if dispatch and dispatch.driver_id else None
            expense = expense_map.get(trip.id)
            fuel_used_l = float(trip.fuel_used_l) if trip.fuel_used_l is not None else None

            distance_km = float(trip.distance_km) if trip.distance_km is not None else None
            if distance_km is None and expense and expense.mileage_km is not None:
                distance_km = float(expense.mileage_km)

            result.append({
                'trip_id': trip.id,
                'passenger_name': passenger.name if passenger else '未知乘客',
                'driver_name': driver.name if driver else '未知司机',
                'purpose': application.purpose if application else None,
                'distance_km': distance_km,
                'fuel_used_l': fuel_used_l,
                'total_cost': float(trip.total_cost) if trip.total_cost is not None else float(expense.total_cost) if expense and expense.total_cost is not None else 0.0,
                'passenger_picked_up': bool(trip.passenger_picked_up),
                'actual_start_time': trip.actual_start_time.isoformat() if trip.actual_start_time else None,
                'actual_end_time': trip.actual_end_time.isoformat() if trip.actual_end_time else None,
                'created_at': trip.created_at.isoformat() if trip.created_at else None
            })

        return jsonify({'success': True, 'data': result})
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
            passenger_picked_up=False,
            status='started'
        )
        db.session.add(trip)
        db.session.commit()
        return jsonify({'success': True, 'data': trip.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


# 司机确认“已接到乘客”并记录行程开始时间
def pickup_passenger(id):
    try:
        trip = Trip.query.get(id)
        if not trip:
            return jsonify({'success': False, 'message': '出车记录不存在'})

        if _enum_value(trip.status) == 'completed':
            return jsonify({'success': False, 'message': '该行程已结束，不能再接乘客'})

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
                return jsonify({'success': False, 'message': '仅该行程司机可确认接到乘客'}), 403

        if trip.passenger_picked_up or trip.actual_start_time is not None:
            if not trip.passenger_picked_up:
                trip.passenger_picked_up = True
                db.session.commit()
            return jsonify({'success': True, 'message': '已确认接到乘客', 'data': trip.to_dict()})

        trip.passenger_picked_up = True
        trip.actual_start_time = datetime.utcnow()
        db.session.commit()
        return jsonify({'success': True, 'message': '已确认接到乘客', 'data': trip.to_dict()})
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

        picked_up = bool(trip.passenger_picked_up) or (trip.actual_start_time is not None)
        if not picked_up:
            return jsonify({'success': False, 'message': '请先确认已接到乘客，再结束行程'}), 400
        if not trip.passenger_picked_up:
            trip.passenger_picked_up = True
        
        # 更新出车记录（支持司机按“消耗路程/消耗油量”录入）
        distance_input = data.get('distance_km')
        fuel_used_input = data.get('fuel_used')
        if distance_input is None:
            return jsonify({'success': False, 'message': '请填写消耗路程'}), 400

        mileage = float(distance_input)
        if mileage < 0:
            return jsonify({'success': False, 'message': '消耗路程不能为负数'}), 400

        fuel_used_value = float(fuel_used_input) if fuel_used_input is not None else 0.0
        if fuel_used_value < 0:
            return jsonify({'success': False, 'message': '消耗油量不能为负数'}), 400

        trip.actual_end_time = datetime.utcnow()
        trip.ended_by = current_user_id
        trip.status = 'completed'
        trip.distance_km = mileage
        trip.fuel_used_l = fuel_used_value
        
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
            fuel_cost = mileage * cost_per_km
        elif vehicle and vehicle.fuel_consumption_per_100km is not None:
            cost_per_km = float(vehicle.fuel_consumption_per_100km) / 100 * fuel_price_value
            fuel_cost = mileage * cost_per_km
        else:
            fuel_used = max(float(fuel_used_value), 0)
            fuel_cost = fuel_used * fuel_price_value if fuel_price_value > 0 else 0.0
            cost_per_km = (fuel_cost / mileage) if mileage > 0 else 0.0

        # 维护费用（可由前端传入，默认 0）
        maintenance_cost = float(data.get('maintenance_cost', 0))
        
        # 其他费用
        other_cost = float(data.get('other_cost', 0))
        
        # 总费用
        total_cost = fuel_cost + maintenance_cost + other_cost
        trip.total_cost = total_cost
        
        # 费用记录：已存在则更新，不存在则创建
        expense = Expense.query.filter_by(trip_id=id).first()
        if not expense:
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
        else:
            expense.mileage_km = mileage
            expense.cost_per_km = cost_per_km
            expense.fuel_cost = fuel_cost
            expense.maintenance_cost = maintenance_cost
            expense.other_cost = other_cost
            expense.total_cost = total_cost
            expense.fuel_price = fuel_price_value
        
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
        data = request.json or {}
        fuel_type = data.get('fuel_type')
        price_value = data.get('price')
        effective_date = data.get('effective_date')
        source = data.get('source')

        if not fuel_type or price_value is None or not effective_date:
            return jsonify({'success': False, 'message': 'fuel_type、price、effective_date 必填'}), 400

        price = FuelPrice.query.filter_by(fuel_type=fuel_type, effective_date=effective_date).first()
        if not price:
            price = FuelPrice(
                fuel_type=fuel_type,
                price=price_value,
                effective_date=effective_date,
                source=source
            )
            db.session.add(price)
        else:
            price.price = price_value
            if source:
                price.source = source

        db.session.commit()
        return jsonify({'success': True, 'data': price.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})
