# 用户管理控制器
from flask import request, jsonify
from models.index import db, User, Department, RoleEnum, UserImportBatch
from flask_bcrypt import generate_password_hash
from flask_jwt_extended import get_jwt_identity
import pandas as pd


def _safe_role(role_value):
    if not role_value:
        return RoleEnum.user
    if isinstance(role_value, RoleEnum):
        return role_value
    try:
        return RoleEnum(role_value)
    except Exception:
        return RoleEnum.user


def _build_username(phone):
    base = str(phone)
    candidate = base
    suffix = 1
    while User.query.filter_by(username=candidate).first():
        suffix += 1
        candidate = f'{base}_{suffix}'
    return candidate


# 获取所有用户
def get_users():
    try:
        users = User.query.filter_by(is_deleted=False).all()
        return jsonify({'success': True, 'data': [user.to_dict() for user in users]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 获取单个用户
def get_user(id):
    try:
        user = User.query.get(id)
        if not user or user.is_deleted:
            return jsonify({'success': False, 'message': '用户不存在'})
        return jsonify({'success': True, 'data': user.to_dict()})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 创建用户
def create_user():
    try:
        data = request.json
        name = data.get('name')
        phone = data.get('phone')
        if not name or not phone:
            return jsonify({'success': False, 'message': '姓名和手机号为必填项'}), 400

        if User.query.filter_by(phone=phone).first():
            return jsonify({'success': False, 'message': '手机号已存在'}), 400

        username = data.get('username') or _build_username(phone)
        if User.query.filter_by(username=username).first():
            return jsonify({'success': False, 'message': '用户名已存在'}), 400

        email = data.get('email')
        if email and User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'message': '邮箱已存在'}), 400

        default_password = str(phone)
        hashed_password = generate_password_hash(default_password).decode('utf-8')
        current_user_id = get_jwt_identity()

        user = User(
            username=username,
            password=hashed_password,
            name=name,
            email=email,
            phone=phone,
            department_id=data.get('department_id'),
            role=_safe_role(data.get('role')),
            created_by=current_user_id
        )
        db.session.add(user)
        db.session.commit()
        return jsonify({'success': True, 'data': user.to_dict(), 'message': '用户创建成功，默认密码为手机号'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


# 更新用户
def update_user(id):
    try:
        user = User.query.get(id)
        if not user or user.is_deleted:
            return jsonify({'success': False, 'message': '用户不存在'})
        
        data = request.json
        user.name = data.get('name', user.name)
        user.email = data.get('email', user.email)
        user.phone = data.get('phone', user.phone)
        user.department_id = data.get('department_id', user.department_id)
        user.role = _safe_role(data.get('role', user.role))
        user.updated_by = get_jwt_identity()
        
        db.session.commit()
        return jsonify({'success': True, 'data': user.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


# 删除用户
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

            username = str(row.get('username', '')).strip() or _build_username(phone)
            if User.query.filter_by(username=username).first():
                username = _build_username(phone)

            email = str(row.get('email', '')).strip() or None
            if email and User.query.filter_by(email=email).first():
                email = None

            role = _safe_role(str(row.get('role', 'user')).strip() or 'user')
            department_raw = row.get('department_id', None)
            department_id = None if pd.isna(department_raw) else int(department_raw)

            user = User(
                username=username,
                password=generate_password_hash(phone).decode('utf-8'),
                name=name,
                email=email,
                phone=phone,
                department_id=department_id,
                role=role,
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
def get_departments():
    try:
        departments = Department.query.all()
        return jsonify({'success': True, 'data': [dept.to_dict() for dept in departments]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


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