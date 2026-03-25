"""统计报表控制器。"""

# 报表统计控制器
from flask import request, jsonify
from sqlalchemy import func, extract, case
from models.index import db, CarApplication, Expense, Trip, Dispatch, Vehicle, Department, User, RoleEnum


# 部门用车频率统计
# 按部门统计用车频率与累计用车天数
def get_department_usage():
    try:
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
# 按部门统计费用构成（油费/维护费/其他费）
def get_department_expenses():
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

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
            query = query.filter(CarApplication.created_at.between(start_date, end_date))

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


# 车辆使用与费用统计
# 按车辆统计使用次数、里程与费用
def get_vehicle_usage():
    try:
        stats = db.session.query(
            Dispatch.vehicle_id,
            func.count(Dispatch.id).label('usage_count'),
            func.sum(func.coalesce(Trip.distance_km, 0)).label('total_mileage'),
            func.sum(Expense.total_cost).label('total_expense')
        ).join(
            Trip, Dispatch.id == Trip.dispatch_id
        ).outerjoin(
            Expense, Expense.trip_id == Trip.id
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
                'total_mileage': float(stat.total_mileage or 0),
                'total_expense': float(stat.total_expense or 0)
            })

        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 月度用车统计
# 月度统计：申请量与总费用
def get_monthly_stats():
    try:
        year = request.args.get('year')
        if year:
            year = int(year)
        else:
            year = db.session.query(func.year(func.now())).scalar()

        stats = db.session.query(
            extract('month', CarApplication.created_at).label('month'),
            func.count(CarApplication.id).label('application_count'),
            func.sum(Expense.total_cost).label('total_expense')
        ).join(
            Dispatch, CarApplication.id == Dispatch.application_id
        ).join(
            Trip, Dispatch.id == Trip.dispatch_id
        ).outerjoin(
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
# 司机工作量统计：行程数与里程
def get_driver_workload():
    try:
        stats = db.session.query(
            Dispatch.driver_id,
            func.count(Dispatch.id).label('trip_count'),
            func.sum(func.coalesce(Trip.distance_km, 0)).label('total_mileage')
        ).join(
            Trip, Dispatch.id == Trip.dispatch_id
        ).filter(
            Trip.status == 'completed'
        ).group_by(Dispatch.driver_id).all()

        result = []
        for stat in stats:
            driver = User.query.filter_by(id=stat.driver_id, role=RoleEnum.driver, is_deleted=False).first()
            result.append({
                'driver_id': stat.driver_id,
                'driver_name': driver.name if driver else '未知司机',
                'trip_count': stat.trip_count,
                'total_mileage': float(stat.total_mileage or 0)
            })

        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 用户申请次数/用车次数/总费用统计（可视化）
# 用户用车画像：申请次数、实际用车次数、总费用
def get_user_application_stats():
    try:
        stats = db.session.query(
            User.id.label('user_id'),
            User.name.label('user_name'),
            func.count(func.distinct(CarApplication.id)).label('application_count'),
            func.sum(case((CarApplication.status.in_(['dispatched', 'completed']), 1), else_=0)).label('usage_count'),
            func.sum(Expense.total_cost).label('total_expense')
        ).outerjoin(
            CarApplication, CarApplication.applicant_id == User.id
        ).outerjoin(
            Dispatch, Dispatch.application_id == CarApplication.id
        ).outerjoin(
            Trip, Trip.dispatch_id == Dispatch.id
        ).outerjoin(
            Expense, Expense.trip_id == Trip.id
        ).filter(
            User.is_deleted == False
        ).group_by(User.id, User.name).all()

        result = []
        for stat in stats:
            result.append({
                'user_id': stat.user_id,
                'user_name': stat.user_name,
                'application_count': int(stat.application_count or 0),
                'usage_count': int(stat.usage_count or 0),
                'total_expense': float(stat.total_expense or 0)
            })

        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
