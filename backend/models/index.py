# 定义数据库模型
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import enum

db = SQLAlchemy()


# 定义角色枚举
class RoleEnum(enum.Enum):
    user = 'user'
    leader = 'leader'
    admin = 'admin'


# 定义车辆状态枚举
class VehicleStatusEnum(enum.Enum):
    available = 'available'
    in_use = 'in_use'
    maintenance = 'maintenance'
    unavailable = 'unavailable'


# 定义司机状态枚举
class DriverStatusEnum(enum.Enum):
    available = 'available'
    busy = 'busy'
    off = 'off'


# 定义申请状态枚举
class ApplicationStatusEnum(enum.Enum):
    pending = 'pending'
    approved = 'approved'
    rejected = 'rejected'
    dispatched = 'dispatched'
    completed = 'completed'
    cancelled = 'cancelled'


# 定义审批结果枚举
class ApprovalStatusEnum(enum.Enum):
    approved = 'approved'
    rejected = 'rejected'


# 定义调度状态枚举
class DispatchStatusEnum(enum.Enum):
    scheduled = 'scheduled'
    in_progress = 'in_progress'
    completed = 'completed'
    cancelled = 'cancelled'


# 定义出车状态枚举
class TripStatusEnum(enum.Enum):
    started = 'started'
    completed = 'completed'


# 用户表模型
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    department_id = db.Column(db.Integer, nullable=False)
    role = db.Column(db.Enum(RoleEnum), nullable=False)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'department_id': self.department_id,
            'role': self.role.value if self.role else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# 部门表模型
class Department(db.Model):
    __tablename__ = 'departments'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    leader_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'leader_id': self.leader_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# 车辆表模型
class Vehicle(db.Model):
    __tablename__ = 'vehicles'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    plate_number = db.Column(db.String(20), unique=True, nullable=False)
    model = db.Column(db.String(50), nullable=False)
    brand = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(20), nullable=False)
    status = db.Column(db.Enum(VehicleStatusEnum), default=VehicleStatusEnum.available)
    purchase_date = db.Column(db.Date, nullable=False)
    last_maintenance_date = db.Column(db.Date, nullable=True)
    fuel_type = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'plate_number': self.plate_number,
            'model': self.model,
            'brand': self.brand,
            'color': self.color,
            'status': self.status.value if self.status else None,
            'purchase_date': self.purchase_date.isoformat() if self.purchase_date else None,
            'last_maintenance_date': self.last_maintenance_date.isoformat() if self.last_maintenance_date else None,
            'fuel_type': self.fuel_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# 司机表模型
class Driver(db.Model):
    __tablename__ = 'drivers'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    license_number = db.Column(db.String(20), unique=True, nullable=False)
    status = db.Column(db.Enum(DriverStatusEnum), default=DriverStatusEnum.available)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'license_number': self.license_number,
            'status': self.status.value if self.status else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# 用车申请表模型
class CarApplication(db.Model):
    __tablename__ = 'car_applications'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    applicant_id = db.Column(db.Integer, nullable=False)
    department_id = db.Column(db.Integer, nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    purpose = db.Column(db.String(200), nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    passenger_count = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Enum(ApplicationStatusEnum), default=ApplicationStatusEnum.pending)
    approval_comment = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'applicant_id': self.applicant_id,
            'department_id': self.department_id,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'purpose': self.purpose,
            'destination': self.destination,
            'passenger_count': self.passenger_count,
            'status': self.status.value if self.status else None,
            'approval_comment': self.approval_comment,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# 审批记录表模型
class Approval(db.Model):
    __tablename__ = 'approvals'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    application_id = db.Column(db.Integer, nullable=False)
    approver_id = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Enum(ApprovalStatusEnum), nullable=False)
    comment = db.Column(db.String(200), nullable=True)
    approved_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'application_id': self.application_id,
            'approver_id': self.approver_id,
            'status': self.status.value if self.status else None,
            'comment': self.comment,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None
        }


# 调度表模型
class Dispatch(db.Model):
    __tablename__ = 'dispatches'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    application_id = db.Column(db.Integer, nullable=False)
    vehicle_id = db.Column(db.Integer, nullable=False)
    driver_id = db.Column(db.Integer, nullable=False)
    dispatcher_id = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Enum(DispatchStatusEnum), default=DispatchStatusEnum.scheduled)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'application_id': self.application_id,
            'vehicle_id': self.vehicle_id,
            'driver_id': self.driver_id,
            'dispatcher_id': self.dispatcher_id,
            'status': self.status.value if self.status else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# 出车记录表模型
class Trip(db.Model):
    __tablename__ = 'trips'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    dispatch_id = db.Column(db.Integer, nullable=False)
    start_mileage = db.Column(db.DECIMAL(10, 2), nullable=False)
    end_mileage = db.Column(db.DECIMAL(10, 2), nullable=True)
    start_fuel = db.Column(db.DECIMAL(10, 2), nullable=False)
    end_fuel = db.Column(db.DECIMAL(10, 2), nullable=True)
    actual_start_time = db.Column(db.DateTime, nullable=True)
    actual_end_time = db.Column(db.DateTime, nullable=True)
    ended_by = db.Column(db.Integer, nullable=True)
    status = db.Column(db.Enum(TripStatusEnum), default=TripStatusEnum.started)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'dispatch_id': self.dispatch_id,
            'start_mileage': float(self.start_mileage) if self.start_mileage else None,
            'end_mileage': float(self.end_mileage) if self.end_mileage else None,
            'start_fuel': float(self.start_fuel) if self.start_fuel else None,
            'end_fuel': float(self.end_fuel) if self.end_fuel else None,
            'actual_start_time': self.actual_start_time.isoformat() if self.actual_start_time else None,
            'actual_end_time': self.actual_end_time.isoformat() if self.actual_end_time else None,
            'ended_by': self.ended_by,
            'status': self.status.value if self.status else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# 费用表模型
class Expense(db.Model):
    __tablename__ = 'expenses'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    trip_id = db.Column(db.Integer, nullable=False)
    fuel_cost = db.Column(db.DECIMAL(10, 2), default=0.00)
    maintenance_cost = db.Column(db.DECIMAL(10, 2), default=0.00)
    other_cost = db.Column(db.DECIMAL(10, 2), default=0.00)
    total_cost = db.Column(db.DECIMAL(10, 2), default=0.00)
    fuel_price = db.Column(db.DECIMAL(10, 2), nullable=False)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'trip_id': self.trip_id,
            'fuel_cost': float(self.fuel_cost) if self.fuel_cost else 0.00,
            'maintenance_cost': float(self.maintenance_cost) if self.maintenance_cost else 0.00,
            'other_cost': float(self.other_cost) if self.other_cost else 0.00,
            'total_cost': float(self.total_cost) if self.total_cost else 0.00,
            'fuel_price': float(self.fuel_price) if self.fuel_price else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# 燃油价格表模型
class FuelPrice(db.Model):
    __tablename__ = 'fuel_prices'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fuel_type = db.Column(db.String(20), nullable=False)
    price = db.Column(db.DECIMAL(10, 2), nullable=False)
    effective_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'fuel_type': self.fuel_type,
            'price': float(self.price) if self.price else None,
            'effective_date': self.effective_date.isoformat() if self.effective_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
