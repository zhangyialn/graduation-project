# 出车记录和费用管理控制器
from flask import request, jsonify
from models.index import db, Trip, Expense, Dispatch, Vehicle, Driver, FuelPrice
from flask_jwt_extended import jwt_required


# 获取所有出车记录
@jwt_required()
def get_trips():
    try:
        trips = Trip.query.all()
        return jsonify({'success': True, 'data': [trip.to_dict() for trip in trips]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 获取单个出车记录
@jwt_required()
def get_trip(id):
    try:
        trip = Trip.query.get(id)
        if not trip:
            return jsonify({'success': False, 'message': '出车记录不存在'})
        return jsonify({'success': True, 'data': trip.to_dict()})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 创建出车记录
@jwt_required()
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
@jwt_required()
def end_trip(id):
    try:
        trip = Trip.query.get(id)
        if not trip:
            return jsonify({'success': False, 'message': '出车记录不存在'})
        
        if trip.status == 'completed':
            return jsonify({'success': False, 'message': '该行程已结束'})
        
        data = request.json
        
        # 更新出车记录
        trip.end_mileage = data['end_mileage']
        trip.end_fuel = data['end_fuel']
        trip.actual_end_time = data.get('actual_end_time')
        trip.ended_by = data['ended_by']
        trip.status = 'completed'
        
        # 获取调度信息
        dispatch = Dispatch.query.get(trip.dispatch_id)
        if dispatch:
            # 更新车辆状态为可用
            vehicle = Vehicle.query.get(dispatch.vehicle_id)
            if vehicle:
                vehicle.status = 'available'
            
            # 更新司机状态为可用
            driver = Driver.query.get(dispatch.driver_id)
            if driver:
                driver.status = 'available'
            
            # 更新调度状态为已完成
            dispatch.status = 'completed'
        
        # 计算费用
        fuel_price = FuelPrice.query.filter_by(
            fuel_type=vehicle.fuel_type if vehicle else '汽油'
        ).order_by(FuelPrice.effective_date.desc()).first()
        
        fuel_price_value = fuel_price.price if fuel_price else 0
        
        # 计算燃油费用
        fuel_consumed = trip.start_fuel - trip.end_mileage
        fuel_cost = fuel_consumed * fuel_price_value
        
        # 计算维护费用（假设每公里0.1元）
        mileage = trip.end_mileage - trip.start_mileage
        maintenance_cost = mileage * 0.1
        
        # 其他费用
        other_cost = data.get('other_cost', 0)
        
        # 总费用
        total_cost = fuel_cost + maintenance_cost + other_cost
        
        # 创建费用记录
        expense = Expense(
            trip_id=id,
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
@jwt_required()
def get_trip_expense(id):
    try:
        expense = Expense.query.filter_by(trip_id=id).first()
        if not expense:
            return jsonify({'success': False, 'message': '费用记录不存在'})
        return jsonify({'success': True, 'data': expense.to_dict()})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 更新费用（用于添加过路费等其他费用）
@jwt_required()
def update_trip_expense(id):
    try:
        expense = Expense.query.filter_by(trip_id=id).first()
        if not expense:
            return jsonify({'success': False, 'message': '费用记录不存在'})
        
        data = request.json
        expense.other_cost = data.get('other_cost', expense.other_cost)
        expense.total_cost = expense.fuel_cost + expense.maintenance_cost + expense.other_cost
        
        db.session.commit()
        return jsonify({'success': True, 'data': expense.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


# ==================== 燃油价格管理 ====================

# 获取燃油价格列表
@jwt_required()
def get_fuel_prices():
    try:
        prices = FuelPrice.query.all()
        return jsonify({'success': True, 'data': [price.to_dict() for price in prices]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 添加燃油价格
@jwt_required()
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