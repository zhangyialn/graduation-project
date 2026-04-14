"""认证与管理员初始化控制器。

包含登录、改密、找回密码，以及“首个管理员初始化”相关的安全校验逻辑。
"""

# 认证控制器
from flask import request, jsonify, current_app
from models.index import db, User, RoleEnum
from flask_bcrypt import check_password_hash, generate_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import hashlib
import secrets
import time


BOOTSTRAP_NONCE_USED_AT = {}


def _normalize_identity(identity):
    if identity is None:
        return None
    try:
        return int(identity)
    except Exception:
        return identity


# 统一密码校验入口：优先按哈希校验，并兼容历史明文密码
def _verify_password(user, plain_password):
    stored_password = str(user.password or '')
    try:
        if check_password_hash(stored_password, plain_password):
            return True, False
    except ValueError:
        pass
    except Exception:
        pass

    if stored_password == str(plain_password):
        return True, True

    return False, False


# 判断系统是否已存在有效管理员，用于控制初始化入口是否关闭
def _has_admin_user():
    return User.query.filter_by(role=RoleEnum.admin, is_deleted=False).first() is not None


# 生成/验证一次性初始化密钥所用的签名器
def _bootstrap_serializer():
    return URLSafeTimedSerializer(
        secret_key=current_app.config.get('JWT_SECRET_KEY', 'bootstrap-secret'),
        salt='bootstrap-admin-key-v1'
    )


# 对绑定信息做摘要，避免在 token 里明文暴露
def _hash_text(value):
    return hashlib.sha256(str(value or '').encode('utf-8')).hexdigest()


# 获取客户端 IP（用于本地/内网访问限制）
def _client_ip():
    return request.remote_addr or ''


# 获取客户端 UA（用于浏览器绑定）
def _client_ua():
    return request.headers.get('User-Agent', '')[:256]


# 判断 IP 是否属于本机或常见内网网段
def _is_private_or_local_ip(ip):
    if not ip:
        return False
    if ip in ('127.0.0.1', '::1'):
        return True
    if ip.startswith('10.') or ip.startswith('192.168.'):
        return True
    if ip.startswith('172.'):
        try:
            second = int(ip.split('.')[1])
            return 16 <= second <= 31
        except Exception:
            return False
    return False


# 清理已使用 nonce 的过期记录，防止内存字典无限增长
def _cleanup_used_nonce_cache(ttl_seconds=7200):
    now = int(time.time())
    expired = [nonce for nonce, used_at in BOOTSTRAP_NONCE_USED_AT.items() if now - used_at > ttl_seconds]
    for nonce in expired:
        BOOTSTRAP_NONCE_USED_AT.pop(nonce, None)


# 用户注册
# 注册普通用户（管理员可通过独立初始化流程创建）
def register():
    try:
        data = request.json
        
        # 检查用户名是否已存在
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'success': False, 'message': '用户名已存在'}), 400
        
        # 检查邮箱是否已存在
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'success': False, 'message': '邮箱已存在'}), 400
        
        # 加密密码
        hashed_password = generate_password_hash(data['password']).decode('utf-8')
        
        # 创建用户
        user = User(
            username=data['username'],
            password=hashed_password,
            name=data['name'],
            email=data['email'],
            phone=data['phone'],
            department_id=data['department_id'],
            role=data.get('role', 'user'),
            must_change_password=False
        )
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '注册成功',
            'data': user.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# 用户登录
# 登录并签发访问令牌；兼容历史明文密码自动升级为哈希
def login():
    try:
        data = request.json
        user = User.query.filter_by(username=data['username']).first()
        
        if not user:
            return jsonify({'success': False, 'message': '用户名或密码错误'}), 401

        if user.is_deleted:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        # 验证密码（兼容历史明文密码）
        verified, need_upgrade = _verify_password(user, data['password'])
        if not verified:
            return jsonify({'success': False, 'message': '用户名或密码错误'}), 401

        # 历史明文密码登录成功后自动升级为哈希
        if need_upgrade:
            try:
                user.password = generate_password_hash(data['password']).decode('utf-8')
                db.session.commit()
            except Exception:
                db.session.rollback()
        
        # 创建访问令牌和刷新令牌
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        
        return jsonify({
            'success': True,
            'message': '登录成功',
            'data': {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': user.to_dict()
            }
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# 刷新令牌
# 使用刷新令牌换取新的访问令牌
def refresh():
    try:
        current_user_id = _normalize_identity(get_jwt_identity())
        access_token = create_access_token(identity=str(current_user_id))
        
        return jsonify({
            'success': True,
            'data': {
                'access_token': access_token
            }
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# 获取当前用户信息
# 获取当前登录用户的最新资料
def get_current_user():
    try:
        current_user_id = _normalize_identity(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        return jsonify({
            'success': True,
            'data': user.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# 修改密码
# 已登录用户主动修改密码
def change_password():
    try:
        current_user_id = _normalize_identity(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        data = request.json
        
        # 验证旧密码
        verified, _need_upgrade = _verify_password(user, data['old_password'])
        if not verified:
            return jsonify({'success': False, 'message': '旧密码错误'}), 400
        
        # 加密新密码
        hashed_password = generate_password_hash(data['new_password']).decode('utf-8')
        user.password = hashed_password
        user.must_change_password = False
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '密码修改成功'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# 账号设置：同一入口修改用户名和/或密码
def update_account_settings():
    try:
        current_user_id = _normalize_identity(get_jwt_identity())
        user = User.query.get(current_user_id)

        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404

        data = request.json or {}
        old_password = str(data.get('old_password') or '')
        username = str(data.get('username') or '').strip()
        new_password = str(data.get('new_password') or '').strip()
        username_changed = bool(username and username != user.username)
        wants_change_password = bool(new_password)

        if not username_changed and not wants_change_password:
            return jsonify({'success': False, 'message': '请至少修改一项（用户名或密码）'}), 400

        if username_changed:
            exists_user = User.query.filter(User.username == username, User.id != user.id).first()
            if exists_user:
                return jsonify({'success': False, 'message': '用户名已存在'}), 400
            user.username = username

        if wants_change_password:
            verified, _need_upgrade = _verify_password(user, old_password)
            if not verified:
                return jsonify({'success': False, 'message': '当前密码错误'}), 400
            if len(new_password) < 6:
                return jsonify({'success': False, 'message': '新密码至少6位'}), 400
            user.password = generate_password_hash(new_password).decode('utf-8')
            user.must_change_password = False

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '账号设置已更新',
            'data': user.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# 验证手机号是否匹配用户名（找回密码步骤1）
# 找回密码第 1 步：校验“用户名 + 手机号”是否匹配
def verify_phone():
    try:
        data = request.json
        user = User.query.filter_by(username=data['username'], phone=data['phone']).first()
        if not user:
            return jsonify({'success': False, 'message': '用户名与手机号不匹配'}), 400
        return jsonify({'success': True, 'message': '验证通过'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# 重置密码（找回密码步骤2）
# 找回密码第 2 步：重置为新密码
def reset_password():
    try:
        data = request.json
        user = User.query.filter_by(username=data['username'], phone=data['phone']).first()
        if not user:
            return jsonify({'success': False, 'message': '用户名与手机号不匹配'}), 400

        hashed_password = generate_password_hash(data['new_password']).decode('utf-8')
        user.password = hashed_password
        user.must_change_password = False
        db.session.commit()

        return jsonify({'success': True, 'message': '密码已重置，请使用新密码登录'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# 首个管理员初始化：仅在系统无管理员时开放，且要求一次性密钥校验通过
def bootstrap_admin():
    try:
        if _has_admin_user():
            return jsonify({'success': False, 'message': '系统已存在管理员，初始化入口已关闭'}), 400

        local_only = bool(current_app.config.get('BOOTSTRAP_LOCAL_ONLY', True))
        ip = _client_ip()
        ua = _client_ua()
        if local_only and not _is_private_or_local_ip(ip):
            return jsonify({'success': False, 'message': '初始化仅允许在内网或本机访问'}), 403

        data = request.json or {}
        username = str(data.get('username') or '').strip()
        password = str(data.get('password') or '').strip()
        name = str(data.get('name') or '').strip()
        phone = str(data.get('phone') or '').strip()
        email = str(data.get('email') or '').strip() or None
        bootstrap_key = str(data.get('bootstrap_key') or '').strip()

        if not username or not password or not name or not phone:
            return jsonify({'success': False, 'message': 'username、password、name、phone 为必填项'}), 400

        if not bootstrap_key:
            return jsonify({'success': False, 'message': '请先在页面生成一次性初始化密钥'}), 400

        serializer = _bootstrap_serializer()
        max_age = int(current_app.config.get('BOOTSTRAP_TOKEN_EXPIRES', 600))
        try:
            payload = serializer.loads(bootstrap_key, max_age=max_age)
        except SignatureExpired:
            return jsonify({'success': False, 'message': '初始化密钥已过期，请重新生成'}), 400
        except BadSignature:
            return jsonify({'success': False, 'message': '初始化密钥无效'}), 400

        _cleanup_used_nonce_cache()
        nonce = str(payload.get('nonce') or '')
        if not nonce:
            return jsonify({'success': False, 'message': '初始化密钥无效'}), 400
        if nonce in BOOTSTRAP_NONCE_USED_AT:
            return jsonify({'success': False, 'message': '初始化密钥已使用，请重新生成'}), 400

        if payload.get('ua_hash') != _hash_text(ua):
            return jsonify({'success': False, 'message': '初始化密钥与当前浏览器不匹配'}), 400

        configured_key = str(current_app.config.get('BOOTSTRAP_ADMIN_KEY') or '').strip()
        if configured_key:
            provided_master = str(data.get('bootstrap_master_key') or '').strip()
            if provided_master != configured_key:
                return jsonify({'success': False, 'message': '主初始化密钥错误'}), 400

        if User.query.filter_by(username=username).first():
            return jsonify({'success': False, 'message': '用户名已存在'}), 400

        if User.query.filter_by(phone=phone).first():
            return jsonify({'success': False, 'message': '手机号已存在'}), 400

        if email and User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'message': '邮箱已存在'}), 400

        user = User(
            username=username,
            password=generate_password_hash(password).decode('utf-8'),
            name=name,
            email=email,
            phone=phone,
            department_id=data.get('department_id'),
            role=RoleEnum.admin,
            must_change_password=False,
            created_by=None
        )
        db.session.add(user)
        db.session.commit()
        BOOTSTRAP_NONCE_USED_AT[nonce] = int(time.time())

        return jsonify({'success': True, 'message': '首个管理员初始化成功', 'data': user.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# 生成一次性初始化密钥（绑定当前浏览器并带有效期）
def generate_bootstrap_key():
    try:
        if _has_admin_user():
            return jsonify({'success': False, 'message': '系统已存在管理员，初始化入口已关闭'}), 400

        local_only = bool(current_app.config.get('BOOTSTRAP_LOCAL_ONLY', True))
        ip = _client_ip()
        ua = _client_ua()
        if local_only and not _is_private_or_local_ip(ip):
            return jsonify({'success': False, 'message': '初始化仅允许在内网或本机访问'}), 403

        nonce = secrets.token_urlsafe(24)
        serializer = _bootstrap_serializer()
        token = serializer.dumps({
            'nonce': nonce,
            'ua_hash': _hash_text(ua)
        })
        expires_in = int(current_app.config.get('BOOTSTRAP_TOKEN_EXPIRES', 600))

        return jsonify({
            'success': True,
            'message': '初始化密钥生成成功',
            'data': {
                'bootstrap_key': token,
                'expires_in': expires_in,
                'local_only': local_only
            }
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# 查询初始化入口状态，前端据此决定是否展示“初始化管理员”入口
def get_bootstrap_status():
    try:
        has_admin = _has_admin_user()
        return jsonify({
            'success': True,
            'data': {
                'enabled': not has_admin,
                'reason': '系统已存在管理员，初始化入口已关闭' if has_admin else '可初始化首个管理员'
            }
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# 判断是否处于开发模式（仅开发模式开放角色切换能力）
def _is_development_mode():
    env = str(current_app.config.get('ENV') or '').lower()
    flask_env = str(current_app.config.get('FLASK_ENV') or '').lower()
    return bool(current_app.debug) or env == 'development' or flask_env == 'development'


# 开发模式：读取数据库中可切换的用户列表
def get_dev_users():
    try:
        if not _is_development_mode():
            return jsonify({'success': False, 'message': '仅开发模式可用'}), 403

        users = User.query.filter_by(is_deleted=False, is_active=True).all()
        result = []
        for item in users:
            payload = item.to_dict()
            result.append({
                'id': payload.get('id'),
                'username': payload.get('username'),
                'name': payload.get('name'),
                'role': payload.get('role'),
                'department_id': payload.get('department_id'),
                'must_change_password': payload.get('must_change_password')
            })

        result.sort(key=lambda x: (str(x.get('role') or ''), int(x.get('id') or 0)))
        return jsonify({'success': True, 'data': result}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# 开发模式：切换为数据库中的指定用户并签发新的JWT
def dev_switch_user():
    try:
        if not _is_development_mode():
            return jsonify({'success': False, 'message': '仅开发模式可用'}), 403

        data = request.json or {}
        user_id_raw = data.get('user_id')
        if user_id_raw in [None, '']:
            return jsonify({'success': False, 'message': 'user_id 为必填项'}), 400

        try:
            user_id = int(user_id_raw)
        except Exception:
            return jsonify({'success': False, 'message': 'user_id 必须为整数'}), 400

        user = User.query.get(user_id)
        if not user or user.is_deleted or not user.is_active:
            return jsonify({'success': False, 'message': '目标用户不存在或不可用'}), 404

        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))

        return jsonify({
            'success': True,
            'message': '角色切换成功',
            'data': {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': user.to_dict()
            }
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
