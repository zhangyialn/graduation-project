# 报表统计控制器
from flask import request, jsonify
from sqlalchemy import func, extract
from models.index import db, CarApplication, Expense, Trip, Dispatch, Vehicle, Department
from flask_jwt_extended import jwt_required


# 部门用车频率统计
@jwt_required()
def get_department_usage():
    try:
        # 按部门统计用车次数
        stats = db.session.query(
            CarApplication.department_id,
            func.count(CarApplication.id).label('total_count'),
            func.sum(func.datediff(CarApplication.end_time, CarApplication.start_time)).label('total_days')
        ).filter(
            CarApplication.status.in_(['completed', 'dispatched'])
        ).group_by(CarApplication.department_id).all()
        
        result = []
        for stat in stats:
            department = Department.query.get(stat.department_id)
            result.append({
                'department_id': stat.department_id,
                'department_name': department.name if department else '未知部门',
                'total_count': stat.total_count,
                'total_days': stat.total_days or 0
            })
        
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 部门费用统计
@jwt_required()
def get_department_expenses():
    try:
        # 获取时间范围参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 查询各部门费用
        query = db.session.query(
            CarApplication.department_id,
            func.sum(Expense.total_cost).label('total_expense'),
            func.sum(Expense.fuel_cost).label('fuel_expense'),
            func.sum(Expense.maintenance_cost).label('maintenance_expense'),
            func.sum(Expense.other_cost).label('other_expense')
        ).join(
            Trip, Expense.trip_id == Trip.id
        ).join(
            Dispatch, Trip.dispatch_id == Dispatch.id
        ).join(
            CarApplication, Dispatch.application_id == CarApplication.id
        )
        
        if start_date and end_date:
            query = query.filter(
                CarApplication.created_at.between(start_date, end_date)
            )
        
        stats = query.group_by(CarApplication.department_id).all()
        
        result = []
        for stat in stats:
            department = Department.query.get(stat.department_id)
            result.append({
                'department_id': stat.department_id,
                'department_name': department.name if department else '未知部门',
                'total_expense': float(stat.total_expense or 0),
                'fuel_expense': float(stat.fuel_expense or 0),
                'maintenance_expense': float(stat.maintenance_expense or 0),
                'other_expense': float(stat.other_expense or 0)
            })
        
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 车辆使用统计
@jwt_required()
def get_vehicle_usage():
    try:
        # 统计每辆车的使用次数和总里程
        stats = db.session.query(
            Dispatch.vehicle_id,
            func.count(Dispatch.id).label('usage_count'),
            func.sum(Trip.end_mileage - Trip.start_mileage).label('total_mileage')
        ).join(
            Trip, Dispatch.id == Trip.dispatch_id
        ).filter(
            Trip.status == 'completed'
        ).group_by(Dispatch.vehicle_id).all()
        
        result = []
        for stat in stats:
            vehicle = Vehicle.query.get(stat.vehicle_id)
            result.append({
                'vehicle_id': stat.vehicle_id,
                'plate_number': vehicle.plate_number if vehicle else '未知车辆',
                'model': vehicle.model if vehicle else '',
                'usage_count': stat.usage_count,
                'total_mileage': float(stat.total_mileage or 0)
            })
        
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 月度用车统计
@jwt_required()
def get_monthly_stats():
    try:
        year = request.args.get('year', func.year(func.now()))
        
        # 按月统计用车次数和费用
        stats = db.session.query(
            extract('month', CarApplication.created_at).label('month'),
            func.count(CarApplication.id).label('application_count'),
            func.sum(Expense.total_cost).label('total_expense')
        ).join(
            Dispatch, CarApplication.id == Dispatch.application_id
        ).join(
            Trip, Dispatch.id == Trip.dispatch_id
        ).join(
            Expense, Trip.id == Expense.trip_id
        ).filter(
            extract('year', CarApplication.created_at) == year
        ).group_by(
            extract('month', CarApplication.created_at)
        ).all()
        
        result = []
        for stat in stats:
            result.append({
                'month': int(stat.month),
                'application_count': stat.application_count,
                'total_expense': float(stat.total_expense or 0)
            })
        
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 司机工作量统计
@jwt_required()
def get_driver_workload():
    try:
        # 统计每个司机的出车次数和总里程
        from models.index import Driver
        
        stats = db.session.query(
            Dispatch.driver_id,
            func.count(Dispatch.id).label('trip_count'),
            func.sum(Trip.end_mileage - Trip.start_mileage).label('total_mileage')
        ).join(
            Trip, Dispatch.id == Trip.dispatch_id
        ).filter(
            Trip.status == 'completed'
        ).group_by(Dispatch.driver_id).all()
        
        result = []
        for stat in stats:
            driver = Driver.query.get(stat.driver_id)
            result.append({
                'driver_id': stat.driver_id,
                'driver_name': driver.name if driver else '未知司机',
                'trip_count': stat.trip_count,
                'total_mileage': float(stat.total_mileage or 0)
            })
        
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})# 报表统计控制器
from flask import Blueprint, request, jsonify
from sqlalchemy import func, extract
from models.index import db, CarApplication, Expense, Trip, Dispatch, Vehicle, Department

report_bp = Blueprint('report', __name__, url_prefix='/api/reports')


# 部门用车频率统计
@report_bp.route('/department-usage', methods=['GET'])
def get_department_usage():
    try:
        # 按部门统计用车次数
        stats = db.session.query(
            CarApplication.department_id,
            func.count(CarApplication.id).label('total_count'),
            func.sum(func.datediff(CarApplication.end_time, CarApplication.start_time)).label('total_days')
        ).filter(
            CarApplication.status.in_(['completed', 'dispatched'])
        ).group_by(CarApplication.department_id).all()
        
        result = []
        for stat in stats:
            department = Department.query.get(stat.department_id)
            result.append({
                'department_id': stat.department_id,
                'department_name': department.name if department else '未知部门',
                'total_count': stat.total_count,
                'total_days': stat.total_days or 0
            })
        
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 部门费用统计
@report_bp.route('/department-expenses', methods=['GET'])
def get_department_expenses():
    try:
        # 获取时间范围参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 查询各部门费用
        query = db.session.query(
            CarApplication.department_id,
            func.sum(Expense.total_cost).label('total_expense'),
            func.sum(Expense.fuel_cost).label('fuel_expense'),
            func.sum(Expense.maintenance_cost).label('maintenance_expense'),
            func.sum(Expense.other_cost).label('other_expense')
        ).join(
            Trip, Expense.trip_id == Trip.id
        ).join(
            Dispatch, Trip.dispatch_id == Dispatch.id
        ).join(
            CarApplication, Dispatch.application_id == CarApplication.id
        )
        
        if start_date and end_date:
            query = query.filter(
                CarApplication.created_at.between(start_date, end_date)
            )
        
        stats = query.group_by(CarApplication.department_id).all()
        
        result = []
        for stat in stats:
            department = Department.query.get(stat.department_id)
            result.append({
                'department_id': stat.department_id,
                'department_name': department.name if department else '未知部门',
                'total_expense': float(stat.total_expense or 0),
                'fuel_expense': float(stat.fuel_expense or 0),
                'maintenance_expense': float(stat.maintenance_expense or 0),
                'other_expense': float(stat.other_expense or 0)
            })
        
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 车辆使用统计
@report_bp.route('/vehicle-usage', methods=['GET'])
def get_vehicle_usage():
    try:
        # 统计每辆车的使用次数和总里程
        stats = db.session.query(
            Dispatch.vehicle_id,
            func.count(Dispatch.id).label('usage_count'),
            func.sum(Trip.end_mileage - Trip.start_mileage).label('total_mileage')
        ).join(
            Trip, Dispatch.id == Trip.dispatch_id
        ).filter(
            Trip.status == 'completed'
        ).group_by(Dispatch.vehicle_id).all()
        
        result = []
        for stat in stats:
            vehicle = Vehicle.query.get(stat.vehicle_id)
            result.append({
                'vehicle_id': stat.vehicle_id,
                'plate_number': vehicle.plate_number if vehicle else '未知车辆',
                'model': vehicle.model if vehicle else '',
                'usage_count': stat.usage_count,
                'total_mileage': float(stat.total_mileage or 0)
            })
        
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 月度用车统计
@report_bp.route('/monthly-stats', methods=['GET'])
def get_monthly_stats():
    try:
        year = request.args.get('year', func.year(func.now()))
        
        # 按月统计用车次数和费用
        stats = db.session.query(
            extract('month', CarApplication.created_at).label('month'),
            func.count(CarApplication.id).label('application_count'),
            func.sum(Expense.total_cost).label('total_expense')
        ).join(
            Dispatch, CarApplication.id == Dispatch.application_id
        ).join(
            Trip, Dispatch.id == Trip.dispatch_id
        ).join(
            Expense, Trip.id == Expense.trip_id
        ).filter(
            extract('year', CarApplication.created_at) == year
        ).group_by(
            extract('month', CarApplication.created_at)
        ).all()
        
        result = []
        for stat in stats:
            result.append({
                'month': int(stat.month),
                'application_count': stat.application_count,
                'total_expense': float(stat.total_expense or 0)
            })
        
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 司机工作量统计
@report_bp.route('/driver-workload', methods=['GET'])
def get_driver_workload():
    try:
        # 统计每个司机的出车次数和总里程
        from models.index import Driver
        
        stats = db.session.query(
            Dispatch.driver_id,
            func.count(Dispatch.id).label('trip_count'),
            func.sum(Trip.end_mileage - Trip.start_mileage).label('total_mileage')
        ).join(
            Trip, Dispatch.id == Trip.dispatch_id
        ).filter(
            Trip.status == 'completed'
        ).group_by(Dispatch.driver_id).all()
        
        result = []
        for stat in stats:
            driver = Driver.query.get(stat.driver_id)
            result.append({
                'driver_id': stat.driver_id,
                'driver_name': driver.name if driver else '未知司机',
                'trip_count': stat.trip_count,
                'total_mileage': float(stat.total_mileage or 0)
            })
        
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})