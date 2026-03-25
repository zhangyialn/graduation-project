"""用户与部门管理控制器。"""

# 用户管理控制器
from flask import request, jsonify
from models.index import db, User, Department, RoleEnum, UserImportBatch, Vehicle
from flask_bcrypt import generate_password_hash, check_password_hash
from flask_jwt_extended import get_jwt_identity
import pandas as pd


ALLOWED_IMPORT_ROLES = {RoleEnum.user.value, RoleEnum.approver.value, RoleEnum.driver.value}


# 将输入角色安全映射到系统枚举（兼容旧角色别名）
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


# 依据基础值生成不冲突的用户名
def _build_username(base_value):
    base = str(base_value)
    candidate = base
    suffix = 1
    while User.query.filter_by(username=candidate).first():
        suffix += 1
        candidate = f'{base}_{suffix}'
    return candidate


# 校验导入角色，仅允许 user/approver
def _validate_import_role(role_value):
    role_enum = _safe_role(role_value)
    role_text = role_enum.value
    if role_text not in ALLOWED_IMPORT_ROLES:
        return None
    return role_enum


def _validate_driver_binding(vehicle_id, current_user_id=None):
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
    if current_user_id:
        bound_driver = bound_driver.filter(User.id != int(current_user_id))
    if bound_driver.first():
        return False, '该车辆已绑定其他司机'
    return True, ''


# 校验操作人密码（兼容历史明文）
def _verify_password(stored_password, plain_password):
    try:
        return check_password_hash(str(stored_password or ''), str(plain_password or ''))
    except Exception:
        return str(stored_password or '') == str(plain_password or '')


# 获取所有用户
# 查询用户列表（过滤软删除）
def get_users():
    try:
        users = User.query.filter_by(is_deleted=False).all()
        return jsonify({'success': True, 'data': [user.to_dict() for user in users]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 获取单个用户
# 查询单个用户
def get_user(id):
    try:
        user = User.query.get(id)
        if not user or user.is_deleted:
            return jsonify({'success': False, 'message': '用户不存在'})
        return jsonify({'success': True, 'data': user.to_dict()})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 创建用户
# 创建用户（默认密码为手机号，首次登录强制改密）
def create_user():
    try:
        data = request.json
        name = data.get('name')
        phone = data.get('phone')
        if not name or not phone:
            return jsonify({'success': False, 'message': '姓名和手机号为必填项'}), 400

        if User.query.filter_by(phone=phone).first():
            return jsonify({'success': False, 'message': '手机号已存在'}), 400

        role_enum = _validate_import_role(data.get('role'))
        if role_enum is None:
            return jsonify({'success': False, 'message': '导入功能仅支持创建普通用户(user)、审批员(approver)或司机(driver)'}), 400

        input_username = (data.get('username') or '').strip()
        default_base = name
        username = input_username or _build_username(default_base)
        if User.query.filter_by(username=username).first():
            username = _build_username(default_base)

        email = data.get('email')
        if email and User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'message': '邮箱已存在'}), 400

        default_password = str(phone)
        hashed_password = generate_password_hash(default_password).decode('utf-8')
        current_user_id = get_jwt_identity()

        vehicle_id = data.get('vehicle_id') if role_enum == RoleEnum.driver else None
        if role_enum == RoleEnum.driver:
            ok, message = _validate_driver_binding(vehicle_id)
            if not ok:
                return jsonify({'success': False, 'message': message}), 400

        user = User(
            username=username,
            password=hashed_password,
            name=name,
            email=email,
            phone=phone,
            department_id=data.get('department_id'),
            role=role_enum,
            vehicle_id=int(vehicle_id) if vehicle_id not in [None, ''] else None,
            driver_status='available',
            license_number=(data.get('license_number') or None) if role_enum == RoleEnum.driver else None,
            must_change_password=True,
            created_by=current_user_id
        )
        db.session.add(user)
        db.session.commit()
        return jsonify({'success': True, 'data': user.to_dict(), 'message': '用户创建成功，默认密码为手机号'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


# 更新用户
# 更新用户信息
def update_user(id):
    try:
        user = User.query.get(id)
        if not user or user.is_deleted:
            return jsonify({'success': False, 'message': '用户不存在'})
        
        data = request.json
        next_role = _safe_role(data.get('role', user.role))
        next_vehicle_id = data.get('vehicle_id', user.vehicle_id)
        if next_role == RoleEnum.driver:
            ok, message = _validate_driver_binding(next_vehicle_id, current_user_id=id)
            if not ok:
                return jsonify({'success': False, 'message': message}), 400

        user.name = data.get('name', user.name)
        user.email = data.get('email', user.email)
        user.phone = data.get('phone', user.phone)
        user.department_id = data.get('department_id', user.department_id)
        user.role = next_role
        user.vehicle_id = int(next_vehicle_id) if next_vehicle_id not in [None, ''] else None
        user.license_number = data.get('license_number', user.license_number)
        if next_role != RoleEnum.driver:
            user.vehicle_id = None
            user.driver_status = 'available'
            user.license_number = None
        else:
            user.driver_status = data.get('driver_status', user.driver_status or 'available')
        user.updated_by = get_jwt_identity()
        
        db.session.commit()
        return jsonify({'success': True, 'data': user.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


# 删除用户
# 软删除用户
def delete_user(id):
    try:
        user = User.query.get(id)
        if not user or user.is_deleted:
            return jsonify({'success': False, 'message': '用户不存在'})

        user.is_deleted = True
        user.is_active = False
        user.deleted_at = db.func.now()
        user.deleted_by = get_jwt_identity()
        db.session.commit()
        return jsonify({'success': True, 'message': '用户删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


# Excel导入用户
# Excel 批量导入用户
def import_users_excel():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '请上传Excel文件'}), 400

        file = request.files['file']
        if not file or not file.filename:
            return jsonify({'success': False, 'message': '文件不能为空'}), 400

        if not (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
            return jsonify({'success': False, 'message': '仅支持 .xlsx/.xls 文件'}), 400

        df = pd.read_excel(file)
        required_columns = {'name', 'phone'}
        if not required_columns.issubset(set(df.columns)):
            return jsonify({'success': False, 'message': 'Excel列必须包含: name, phone'}), 400

        current_user_id = get_jwt_identity()
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
            department_raw = row.get('department_id', None)
            department_id = None if pd.isna(department_raw) else int(department_raw)

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

        db.session.commit()
        return jsonify({
            'success': True,
            'message': '导入完成',
            'data': {
                'batch_id': batch.id,
                'total_rows': batch.total_rows,
                'success_rows': batch.success_rows,
                'failed_rows': batch.failed_rows,
                'failures': failure_messages[:20]
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# 部门管理接口
# 查询部门列表
def get_departments():
    try:
        departments = Department.query.all()
        return jsonify({'success': True, 'data': [dept.to_dict() for dept in departments]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 创建部门
def create_department():
    try:
        data = request.json
        department = Department(
            name=data['name'],
            leader_id=data['leader_id']
        )
        db.session.add(department)
        db.session.commit()
        return jsonify({'success': True, 'data': department.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


# 由当前管理员创建新管理员（需二次密码确认）
def create_admin_user():
    try:
        data = request.json or {}
        name = (data.get('name') or '').strip()
        phone = (data.get('phone') or '').strip()
        operator_password = data.get('operator_password')

        if not name or not phone or not operator_password:
            return jsonify({'success': False, 'message': '姓名、手机号、当前管理员密码为必填项'}), 400

        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        if not current_user or current_user.is_deleted:
            return jsonify({'success': False, 'message': '当前管理员不存在'}), 404

        if not _verify_password(current_user.password, operator_password):
            return jsonify({'success': False, 'message': '当前管理员密码错误，无法创建新管理员'}), 400

        if User.query.filter_by(phone=phone).first():
            return jsonify({'success': False, 'message': '手机号已存在'}), 400

        username = (data.get('username') or '').strip() or _build_username(name)
        if User.query.filter_by(username=username).first():
            username = _build_username(name)

        email = (data.get('email') or '').strip() or None
        if email and User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'message': '邮箱已存在'}), 400

        default_password = str(phone)
        hashed_password = generate_password_hash(default_password).decode('utf-8')

        user = User(
            username=username,
            password=hashed_password,
            name=name,
            email=email,
            phone=phone,
            department_id=data.get('department_id'),
            role=RoleEnum.admin,
            must_change_password=True,
            created_by=current_user_id
        )
        db.session.add(user)
        db.session.commit()

        return jsonify({
            'success': True,
            'data': user.to_dict(),
            'message': '管理员创建成功，默认密码为手机号'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})
