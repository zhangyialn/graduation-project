# 认证控制器
from flask import request, jsonify, current_app
from models.index import db, User
from flask_bcrypt import check_password_hash, generate_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity


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


# 用户注册
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
            role=data.get('role', 'user')
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
def login():
    try:
        data = request.json
        user = User.query.filter_by(username=data['username']).first()
        
        if not user:
            return jsonify({'success': False, 'message': '用户名或密码错误'}), 401
        
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
def refresh():
    try:
        current_user_id = get_jwt_identity()
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
def get_current_user():
    try:
        current_user_id = get_jwt_identity()
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
def change_password():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        data = request.json
        
        # 验证旧密码
        if not check_password_hash(user.password, data['old_password']):
            return jsonify({'success': False, 'message': '旧密码错误'}), 400
        
        # 加密新密码
        hashed_password = generate_password_hash(data['new_password']).decode('utf-8')
        user.password = hashed_password
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '密码修改成功'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# 验证手机号是否匹配用户名（找回密码步骤1）
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
def reset_password():
    try:
        data = request.json
        user = User.query.filter_by(username=data['username'], phone=data['phone']).first()
        if not user:
            return jsonify({'success': False, 'message': '用户名与手机号不匹配'}), 400

        hashed_password = generate_password_hash(data['new_password']).decode('utf-8')
        user.password = hashed_password
        db.session.commit()

        return jsonify({'success': True, 'message': '密码已重置，请使用新密码登录'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500