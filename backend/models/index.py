"""数据库模型与业务枚举定义。"""

# 定义数据库模型
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import enum


db = SQLAlchemy()


# 定义角色枚举
# 系统用户角色枚举
class RoleEnum(enum.Enum):
    user = 'user'
    driver = 'driver'
    approver = 'approver'
    admin = 'admin'


# 定义车辆状态枚举
# 车辆状态枚举
class VehicleStatusEnum(enum.Enum):
    available = 'available'
    in_use = 'in_use'
    maintenance = 'maintenance'
    unavailable = 'unavailable'


# 定义司机状态枚举
# 司机状态枚举
class DriverStatusEnum(enum.Enum):
    available = 'available'
    busy = 'busy'
    unavailable = 'unavailable'


# 定义申请状态枚举
# 用车申请状态枚举
class ApplicationStatusEnum(enum.Enum):
    pending = 'pending'
    approved = 'approved'
    rejected = 'rejected'
    dispatched = 'dispatched'
    completed = 'completed'
    cancelled = 'cancelled'


# 定义审批结果枚举
# 审批结果状态枚举
class ApprovalStatusEnum(enum.Enum):
    approved = 'approved'
    rejected = 'rejected'


# 定义调度状态枚举
# 调度状态枚举
class DispatchStatusEnum(enum.Enum):
    scheduled = 'scheduled'
    in_progress = 'in_progress'
    completed = 'completed'
    cancelled = 'cancelled'


# 定义出车状态枚举
# 行程状态枚举
class TripStatusEnum(enum.Enum):
    started = 'started'
    completed = 'completed'


# 用户导入批次表模型（Excel导入）
# 用户导入批次模型（记录一次 Excel 导入过程）
class UserImportBatch(db.Model):
    __tablename__ = 'user_import_batches'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    operator_id = db.Column(db.Integer, nullable=True)
    file_name = db.Column(db.String(255), nullable=True)
    total_rows = db.Column(db.Integer, nullable=False, default=0)
    success_rows = db.Column(db.Integer, nullable=False, default=0)
    failed_rows = db.Column(db.Integer, nullable=False, default=0)
    remark = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    # 转换为前端可直接消费的字典结构
    def to_dict(self):
        return {
            'id': self.id,
            'operator_id': self.operator_id,
            'file_name': self.file_name,
            'total_rows': self.total_rows,
            'success_rows': self.success_rows,
            'failed_rows': self.failed_rows,
            'remark': self.remark,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# 用户表模型
# 用户模型
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=True)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    department_id = db.Column(db.Integer, nullable=True)
    role = db.Column(db.Enum(RoleEnum), nullable=False, default=RoleEnum.user)
    import_batch_id = db.Column(db.Integer, nullable=True)
    must_change_password = db.Column(db.Boolean, nullable=False, default=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)
    created_by = db.Column(db.Integer, nullable=True)
    updated_by = db.Column(db.Integer, nullable=True)
    deleted_by = db.Column(db.Integer, nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 转换为前端可直接消费的字典结构
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'department_id': self.department_id,
            'role': self.role.value if self.role else None,
            'import_batch_id': self.import_batch_id,
            'must_change_password': self.must_change_password,
            'is_active': self.is_active,
            'is_deleted': self.is_deleted,
            'created_by': self.created_by,
            'updated_by': self.updated_by,
            'deleted_by': self.deleted_by,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# 部门表模型
# 部门模型
class Department(db.Model):
    __tablename__ = 'departments'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    leader_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 转换为前端可直接消费的字典结构
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'leader_id': self.leader_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# 车辆表模型
# 车辆模型
class Vehicle(db.Model):
    __tablename__ = 'vehicles'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    plate_number = db.Column(db.String(20), unique=True, nullable=False)
    model = db.Column(db.String(50), nullable=False)
    brand = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(20), nullable=False)
    seat_count = db.Column(db.Integer, nullable=False, default=5)
    status = db.Column(db.Enum(VehicleStatusEnum), default=VehicleStatusEnum.available)
    purchase_date = db.Column(db.Date, nullable=False)
    last_maintenance_date = db.Column(db.Date, nullable=True)
    annual_inspection_date = db.Column(db.Date, nullable=True)
    fuel_type = db.Column(db.String(20), nullable=False)
    fuel_consumption_per_100km = db.Column(db.DECIMAL(6, 2), nullable=True)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)
    created_by = db.Column(db.Integer, nullable=True)
    deleted_by = db.Column(db.Integer, nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 转换为前端可直接消费的字典结构
    def to_dict(self):
        return {
            'id': self.id,
            'plate_number': self.plate_number,
            'model': self.model,
            'brand': self.brand,
            'color': self.color,
            'seat_count': self.seat_count,
            'status': self.status.value if self.status else None,
            'purchase_date': self.purchase_date.isoformat() if self.purchase_date else None,
            'last_maintenance_date': self.last_maintenance_date.isoformat() if self.last_maintenance_date else None,
            'annual_inspection_date': self.annual_inspection_date.isoformat() if self.annual_inspection_date else None,
            'fuel_type': self.fuel_type,
            'fuel_consumption_per_100km': float(self.fuel_consumption_per_100km) if self.fuel_consumption_per_100km else None,
            'is_deleted': self.is_deleted,
            'created_by': self.created_by,
            'deleted_by': self.deleted_by,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# 司机表模型
# 司机模型（与用户、车辆一对一绑定）
class Driver(db.Model):
    __tablename__ = 'drivers'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False, unique=True)
    vehicle_id = db.Column(db.Integer, nullable=False, unique=True)
    name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    license_number = db.Column(db.String(20), unique=True, nullable=False)
    status = db.Column(db.Enum(DriverStatusEnum), default=DriverStatusEnum.available)
    hire_date = db.Column(db.Date, nullable=True)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)
    created_by = db.Column(db.Integer, nullable=True)
    deleted_by = db.Column(db.Integer, nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 转换为前端可直接消费的字典结构
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'vehicle_id': self.vehicle_id,
            'name': self.name,
            'phone': self.phone,
            'license_number': self.license_number,
            'status': self.status.value if self.status else None,
            'hire_date': self.hire_date.isoformat() if self.hire_date else None,
            'is_deleted': self.is_deleted,
            'created_by': self.created_by,
            'deleted_by': self.deleted_by,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# 用车申请表模型
# 用车申请模型
class CarApplication(db.Model):
    __tablename__ = 'car_applications'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    applicant_id = db.Column(db.Integer, nullable=False)
    department_id = db.Column(db.Integer, nullable=True)
    driver_id = db.Column(db.Integer, nullable=False)
    start_point = db.Column(db.String(120), nullable=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    purpose = db.Column(db.String(200), nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    passenger_count = db.Column(db.Integer, nullable=False)
    expected_distance_km = db.Column(db.DECIMAL(10, 2), nullable=True)
    status = db.Column(db.Enum(ApplicationStatusEnum), default=ApplicationStatusEnum.pending)
    approval_comment = db.Column(db.String(200), nullable=True)
    approved_by = db.Column(db.Integer, nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    cancelled_by = db.Column(db.Integer, nullable=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 转换为前端可直接消费的字典结构
    def to_dict(self):
        return {
            'id': self.id,
            'applicant_id': self.applicant_id,
            'department_id': self.department_id,
            'driver_id': self.driver_id,
            'start_point': self.start_point,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'purpose': self.purpose,
            'destination': self.destination,
            'passenger_count': self.passenger_count,
            'expected_distance_km': float(self.expected_distance_km) if self.expected_distance_km else None,
            'status': self.status.value if self.status else None,
            'approval_comment': self.approval_comment,
            'approved_by': self.approved_by,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'cancelled_by': self.cancelled_by,
            'cancelled_at': self.cancelled_at.isoformat() if self.cancelled_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# 审批记录表模型
# 审批记录模型
class Approval(db.Model):
    __tablename__ = 'approvals'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    application_id = db.Column(db.Integer, nullable=False)
    approver_id = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Enum(ApprovalStatusEnum), nullable=False)
    comment = db.Column(db.String(200), nullable=True)
    approved_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    # 转换为前端可直接消费的字典结构
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
# 调度模型
class Dispatch(db.Model):
    __tablename__ = 'dispatches'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    application_id = db.Column(db.Integer, nullable=False)
    vehicle_id = db.Column(db.Integer, nullable=False)
    driver_id = db.Column(db.Integer, nullable=False)
    dispatcher_id = db.Column(db.Integer, nullable=False)
    dispatch_time = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)
    status = db.Column(db.Enum(DispatchStatusEnum), default=DispatchStatusEnum.scheduled)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 转换为前端可直接消费的字典结构
    def to_dict(self):
        return {
            'id': self.id,
            'application_id': self.application_id,
            'vehicle_id': self.vehicle_id,
            'driver_id': self.driver_id,
            'dispatcher_id': self.dispatcher_id,
            'dispatch_time': self.dispatch_time.isoformat() if self.dispatch_time else None,
            'status': self.status.value if self.status else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# 出车记录表模型
# 出车行程模型
class Trip(db.Model):
    __tablename__ = 'trips'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    dispatch_id = db.Column(db.Integer, nullable=False)
    start_mileage = db.Column(db.DECIMAL(10, 2), nullable=False)
    end_mileage = db.Column(db.DECIMAL(10, 2), nullable=True)
    distance_km = db.Column(db.DECIMAL(10, 2), nullable=True)
    start_fuel = db.Column(db.DECIMAL(10, 2), nullable=False)
    end_fuel = db.Column(db.DECIMAL(10, 2), nullable=True)
    actual_start_time = db.Column(db.DateTime, nullable=True)
    actual_end_time = db.Column(db.DateTime, nullable=True)
    ended_by = db.Column(db.Integer, nullable=True)
    status = db.Column(db.Enum(TripStatusEnum), default=TripStatusEnum.started)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 转换为前端可直接消费的字典结构
    def to_dict(self):
        return {
            'id': self.id,
            'dispatch_id': self.dispatch_id,
            'start_mileage': float(self.start_mileage) if self.start_mileage else None,
            'end_mileage': float(self.end_mileage) if self.end_mileage else None,
            'distance_km': float(self.distance_km) if self.distance_km else None,
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
# 费用模型（与行程一对一）
class Expense(db.Model):
    __tablename__ = 'expenses'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    trip_id = db.Column(db.Integer, nullable=False, unique=True)
    mileage_km = db.Column(db.DECIMAL(10, 2), nullable=False, default=0.00)
    cost_per_km = db.Column(db.DECIMAL(10, 4), nullable=False, default=0.0000)
    fuel_price = db.Column(db.DECIMAL(10, 2), nullable=False, default=0.00)
    fuel_cost = db.Column(db.DECIMAL(10, 2), default=0.00)
    maintenance_cost = db.Column(db.DECIMAL(10, 2), default=0.00)
    other_cost = db.Column(db.DECIMAL(10, 2), default=0.00)
    total_cost = db.Column(db.DECIMAL(10, 2), default=0.00)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 转换为前端可直接消费的字典结构
    def to_dict(self):
        return {
            'id': self.id,
            'trip_id': self.trip_id,
            'mileage_km': float(self.mileage_km) if self.mileage_km else 0.00,
            'cost_per_km': float(self.cost_per_km) if self.cost_per_km else 0.00,
            'fuel_price': float(self.fuel_price) if self.fuel_price else 0.00,
            'fuel_cost': float(self.fuel_cost) if self.fuel_cost else 0.00,
            'maintenance_cost': float(self.maintenance_cost) if self.maintenance_cost else 0.00,
            'other_cost': float(self.other_cost) if self.other_cost else 0.00,
            'total_cost': float(self.total_cost) if self.total_cost else 0.00,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# 燃油价格表模型
# 燃油价格模型
class FuelPrice(db.Model):
    __tablename__ = 'fuel_prices'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fuel_type = db.Column(db.String(20), nullable=False)
    price = db.Column(db.DECIMAL(10, 2), nullable=False)
    effective_date = db.Column(db.Date, nullable=False)
    source = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    # 转换为前端可直接消费的字典结构
    def to_dict(self):
        return {
            'id': self.id,
            'fuel_type': self.fuel_type,
            'price': float(self.price) if self.price else None,
            'effective_date': self.effective_date.isoformat() if self.effective_date else None,
            'source': self.source,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
