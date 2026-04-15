"""用户批量导入服务。"""

import pandas as pd
from flask_bcrypt import generate_password_hash
from models.index import db, User, Department, RoleEnum, UserImportBatch, Vehicle


ALLOWED_IMPORT_ROLES = {RoleEnum.user.value, RoleEnum.approver.value, RoleEnum.driver.value}


class UserImportError(Exception):
    """批量导入业务异常。"""

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _safe_role(role_value):
    if not role_value:
        return RoleEnum.user
    if isinstance(role_value, RoleEnum):
        return role_value
    role_text = str(role_value or '').strip().lower()
    if role_text == 'leader':
        return RoleEnum.approver
    if role_text == 'dispatcher':
        return RoleEnum.admin
    try:
        return RoleEnum(role_text)
    except Exception:
        return RoleEnum.user


def _validate_import_role(role_value):
    role_enum = _safe_role(role_value)
    role_text = role_enum.value
    if role_text not in ALLOWED_IMPORT_ROLES:
        return None
    return role_enum


def _build_username(base_value):
    base = str(base_value)
    candidate = base
    suffix = 1
    while User.query.filter_by(username=candidate).first():
        suffix += 1
        candidate = f'{base}_{suffix}'
    return candidate


def _validate_driver_binding(vehicle_id):
    if vehicle_id in [None, '']:
        return False, '司机角色必须绑定车辆'
    vehicle = Vehicle.query.get(int(vehicle_id))
    if not vehicle or vehicle.is_deleted:
        return False, '绑定车辆不存在'
    bound_driver = User.query.filter(
        User.role == RoleEnum.driver,
        User.vehicle_id == int(vehicle_id),
        User.is_deleted == False
    )
    if bound_driver.first():
        return False, '该车辆已绑定其他司机'
    return True, ''


def _validate_excel_file(file):
    if file is None:
        raise UserImportError('请上传Excel文件', 400)
    if not file.filename:
        raise UserImportError('文件不能为空', 400)
    if not (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
        raise UserImportError('仅支持 .xlsx/.xls 文件', 400)


def _read_excel_rows(file):
    df = pd.read_excel(file)
    required_columns = {'name', 'phone', 'department_id', 'department_name'}
    if not required_columns.issubset(set(df.columns)):
        raise UserImportError('Excel列必须包含: name, phone, department_id, department_name', 400)
    return df


def import_users_from_excel_file(file, current_user_id):
    """从 Excel 文件导入用户，不负责 commit/rollback。"""
    _validate_excel_file(file)
    df = _read_excel_rows(file)

    batch = UserImportBatch(
        operator_id=current_user_id,
        file_name=file.filename,
        total_rows=len(df)
    )
    db.session.add(batch)
    db.session.flush()

    success_rows = 0
    failed_rows = 0
    failure_messages = []

    for index, row in df.iterrows():
        name = str(row.get('name', '')).strip()
        phone = str(row.get('phone', '')).strip()
        if not name or not phone:
            failed_rows += 1
            failure_messages.append(f'第{index + 2}行：姓名或手机号为空')
            continue

        if User.query.filter_by(phone=phone).first():
            failed_rows += 1
            failure_messages.append(f'第{index + 2}行：手机号已存在')
            continue

        input_username = str(row.get('username', '')).strip()

        email = str(row.get('email', '')).strip() or None
        if email and User.query.filter_by(email=email).first():
            email = None

        role_value = str(row.get('role', 'user')).strip() or 'user'
        role = _validate_import_role(role_value)
        if role is None:
            failed_rows += 1
            failure_messages.append(f'第{index + 2}行：角色仅支持 user / approver / driver')
            continue

        default_username_base = name
        username = input_username or _build_username(default_username_base)
        if User.query.filter_by(username=username).first():
            username = _build_username(default_username_base)

        department_id_raw = row.get('department_id', None)
        department_name_raw = row.get('department_name', None)
        if pd.isna(department_id_raw) or pd.isna(department_name_raw):
            failed_rows += 1
            failure_messages.append(f'第{index + 2}行：department_id 和 department_name 为必填')
            continue

        try:
            department_id = int(department_id_raw)
        except Exception:
            failed_rows += 1
            failure_messages.append(f'第{index + 2}行：department_id 必须为整数')
            continue

        department_name = str(department_name_raw).strip()
        if not department_name:
            failed_rows += 1
            failure_messages.append(f'第{index + 2}行：department_name 不能为空')
            continue

        department = Department.query.get(department_id)
        if not department:
            failed_rows += 1
            failure_messages.append(f'第{index + 2}行：部门ID不存在，请先创建部门')
            continue

        if str(department.name).strip() != department_name:
            failed_rows += 1
            failure_messages.append(f'第{index + 2}行：department_id 与 department_name 不匹配')
            continue

        vehicle_raw = row.get('vehicle_id', None)
        vehicle_id = None if pd.isna(vehicle_raw) else int(vehicle_raw)
        if role == RoleEnum.driver:
            ok, message = _validate_driver_binding(vehicle_id)
            if not ok:
                failed_rows += 1
                failure_messages.append(f'第{index + 2}行：{message}')
                continue

        license_number = str(row.get('license_number', '')).strip() or None
        if role == RoleEnum.driver and license_number:
            if User.query.filter_by(license_number=license_number, is_deleted=False).first():
                failed_rows += 1
                failure_messages.append(f'第{index + 2}行：驾驶证号已存在')
                continue

        user = User(
            username=username,
            password=generate_password_hash(phone).decode('utf-8'),
            name=name,
            email=email,
            phone=phone,
            department_id=department_id,
            role=role,
            vehicle_id=vehicle_id if role == RoleEnum.driver else None,
            driver_status='available',
            license_number=license_number if role == RoleEnum.driver else None,
            must_change_password=True,
            import_batch_id=batch.id,
            created_by=current_user_id
        )
        db.session.add(user)
        success_rows += 1

    batch.success_rows = success_rows
    batch.failed_rows = failed_rows
    if failure_messages:
        batch.remark = '；'.join(failure_messages[:10])

    return {
        'batch': batch,
        'failure_messages': failure_messages
    }
