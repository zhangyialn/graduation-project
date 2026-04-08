"""用车申请控制器。"""

# 用车申请控制器
from datetime import datetime
from flask import request, jsonify
from models.index import db, CarApplication, User, Vehicle, RoleEnum
from controllers.recommendation_utils import build_driver_recommendations
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json


LOCKED_APPLICATION_STATUSES = ['pending', 'approved', 'dispatched']


# 兼容 Enum/字符串两种状态值读取
def _enum_value(value):
    return value.value if hasattr(value, 'value') else value


# 解析 ISO 时间字符串，兼容带 Z 后缀的 UTC 文本
def _parse_datetime(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).replace('Z', '+00:00')
    return datetime.fromisoformat(text)


# 判断司机是否已绑定到进行中的申请，避免重复占用
def _is_driver_locked(driver_id, exclude_application_id=None):
    query = CarApplication.query.filter(
        CarApplication.driver_id == driver_id,
        CarApplication.status.in_(LOCKED_APPLICATION_STATUSES)
    )
    if exclude_application_id:
        query = query.filter(CarApplication.id != exclude_application_id)
    return query.first() is not None


# 校验司机+车辆是否都可用，并且司机没有冲突申请
def _validate_driver_available(driver_id, exclude_application_id=None):
    driver = User.query.filter_by(id=driver_id, role=RoleEnum.driver, is_deleted=False).first()
    if not driver:
        return False, '司机不存在', None

    if _enum_value(driver.driver_status) != 'available':
        return False, '司机当前不可用', None

    vehicle = Vehicle.query.get(driver.vehicle_id)
    if not vehicle or vehicle.is_deleted:
        return False, '司机绑定车辆不存在', None

    if _enum_value(vehicle.status) != 'available':
        return False, '司机绑定车辆当前不可用', None

    if _is_driver_locked(driver_id, exclude_application_id=exclude_application_id):
        return False, '该司机已有进行中的申请，暂不可重复申请', None

    return True, '', driver


# 本地轻量地址清洗：去空白、去中英文标点
def _simple_normalize_text(text):
    value = str(text or '').strip()
    value = ' '.join(value.split())
    value = value.replace('，', '').replace(',', '').replace('。', '')
    return value


# 将在线地理服务返回的结构化地址拼接为中文文本
def _build_address_text(address=None):
    payload = address or {}
    province = payload.get('state') or payload.get('province') or ''
    city = payload.get('city') or payload.get('town') or payload.get('county') or payload.get('state_district') or ''
    district = payload.get('city_district') or payload.get('suburb') or payload.get('borough') or payload.get('quarter') or ''
    road = payload.get('road') or payload.get('pedestrian') or payload.get('residential') or payload.get('neighbourhood') or ''
    number = payload.get('house_number') or ''
    return ''.join([part for part in [province, city, district, road, number] if part])


# 调用在线地理服务做地址标准化
def _normalize_address_online(text):
    query = urlencode({
        'q': text,
        'format': 'jsonv2',
        'addressdetails': 1,
        'limit': 1,
        'accept-language': 'zh-CN'
    })
    url = f'https://nominatim.openstreetmap.org/search?{query}'
    req = Request(url, headers={'User-Agent': 'graduation-project/1.0'})
    with urlopen(req, timeout=5) as response:
        body = response.read().decode('utf-8')
        data = json.loads(body)
        if not data:
            return None
        top = data[0]
        address_text = _build_address_text(top.get('address'))
        return {
            'normalized_text': address_text or top.get('display_name') or text,
            'latitude': top.get('lat'),
            'longitude': top.get('lon'),
            'raw_display_name': top.get('display_name')
        }


# 获取所有申请
# 查询申请列表（支持按状态筛选）
def get_applications():
    try:
        # 支持按状态筛选
        status = request.args.get('status')
        if status:
            applications = CarApplication.query.filter(CarApplication.status == status).all()
        else:
            applications = CarApplication.query.all()
        return jsonify({'success': True, 'data': [app.to_dict() for app in applications]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 获取单个申请
# 查询单条申请详情
def get_application(id):
    try:
        application = CarApplication.query.get(id)
        if not application:
            return jsonify({'success': False, 'message': '申请不存在'})
        return jsonify({'success': True, 'data': application.to_dict()})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 创建用车申请
# 创建用车申请并校验司机可用性
def create_application():
    try:
        data = request.json
        required_fields = ['applicant_id', 'driver_id', 'start_time', 'purpose', 'destination', 'passenger_count']
        missing = [field for field in required_fields if data.get(field) in [None, '']]
        if missing:
            return jsonify({'success': False, 'message': f'缺少必填字段: {", ".join(missing)}'}), 400

        applicant = User.query.filter_by(id=int(data['applicant_id']), is_deleted=False).first()
        if not applicant:
            return jsonify({'success': False, 'message': '申请人不存在'}), 404
        if applicant.department_id in [None, 0]:
            return jsonify({'success': False, 'message': '申请人未配置所属部门，无法提交申请'}), 400

        request_department_id = data.get('department_id')
        if request_department_id not in [None, ''] and int(request_department_id) != int(applicant.department_id):
            return jsonify({'success': False, 'message': '部门必须与申请人所属部门一致'}), 400

        ok, message, _driver = _validate_driver_available(int(data['driver_id']))
        if not ok:
            return jsonify({'success': False, 'message': message}), 400

        start_time = _parse_datetime(data['start_time'])
        end_time = _parse_datetime(data.get('end_time')) or start_time

        application = CarApplication(
            applicant_id=int(data['applicant_id']),
            department_id=int(applicant.department_id),
            driver_id=int(data['driver_id']),
            start_point=data.get('start_point'),
            start_time=start_time,
            end_time=end_time,
            purpose=data['purpose'],
            destination=data['destination'],
            passenger_count=int(data['passenger_count']),
            expected_distance_km=data.get('expected_distance_km')
        )

        if application.start_time and application.end_time and application.end_time < application.start_time:
            return jsonify({'success': False, 'message': '结束时间不能早于开始时间'}), 400

        db.session.add(application)
        db.session.commit()
        return jsonify({'success': True, 'data': application.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


# 更新申请
# 更新申请（仅待审批状态允许修改）
def update_application(id):
    try:
        application = CarApplication.query.get(id)
        if not application:
            return jsonify({'success': False, 'message': '申请不存在'})
        
        # 只有待审批状态的申请才能修改
        if _enum_value(application.status) != 'pending':
            return jsonify({'success': False, 'message': '只有待审批的申请才能修改'})
        
        data = request.json
        if data.get('driver_id') is not None:
            new_driver_id = int(data['driver_id'])
            ok, message, _driver = _validate_driver_available(new_driver_id, exclude_application_id=id)
            if not ok:
                return jsonify({'success': False, 'message': message}), 400
            application.driver_id = new_driver_id

        if data.get('start_time'):
            application.start_time = _parse_datetime(data.get('start_time'))
        if data.get('end_time'):
            application.end_time = _parse_datetime(data.get('end_time'))

        if application.start_time and application.end_time and application.end_time < application.start_time:
            return jsonify({'success': False, 'message': '结束时间不能早于开始时间'}), 400

        application.start_point = data.get('start_point', application.start_point)
        application.purpose = data.get('purpose', application.purpose)
        application.destination = data.get('destination', application.destination)
        application.passenger_count = data.get('passenger_count', application.passenger_count)
        
        db.session.commit()
        return jsonify({'success': True, 'data': application.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


# 取消申请
# 取消申请（仅 pending/approved 可取消）
def cancel_application(id):
    try:
        application = CarApplication.query.get(id)
        if not application:
            return jsonify({'success': False, 'message': '申请不存在'})
        
        # 只有待审批或已批准的申请才能取消
        if _enum_value(application.status) not in ['pending', 'approved']:
            return jsonify({'success': False, 'message': '当前状态无法取消'})
        
        application.status = 'cancelled'
        db.session.commit()
        return jsonify({'success': True, 'data': application.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


# 获取我的申请列表
# 查询当前用户发起的申请
def get_my_applications(user_id):
    try:
        applications = CarApplication.query.filter_by(applicant_id=user_id).all()
        return jsonify({'success': True, 'data': [app.to_dict() for app in applications]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 获取待审批列表（部门领导使用）
# 查询部门待审批申请
def get_pending_applications(department_id):
    try:
        applications = CarApplication.query.filter_by(
            department_id=department_id,
            status='pending'
        ).all()
        applicant_ids = list({app.applicant_id for app in applications if app.applicant_id})
        users = User.query.filter(User.id.in_(applicant_ids)).all() if applicant_ids else []
        user_map = {user.id: user for user in users}

        result = []
        for app in applications:
            item = app.to_dict()
            applicant = user_map.get(app.applicant_id)
            item['applicant_name'] = applicant.name if applicant else None
            result.append(item)

        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 地址标准化接口：优先在线标准化，失败则回退本地清洗
def normalize_address():
    try:
        data = request.json or {}
        text = _simple_normalize_text(data.get('text'))
        if not text:
            return jsonify({'success': False, 'message': '请输入地址文本'}), 400

        try:
            online = _normalize_address_online(text)
        except Exception:
            online = None

        if online:
            return jsonify({
                'success': True,
                'data': {
                    'original_text': text,
                    'normalized_text': online['normalized_text'],
                    'latitude': online.get('latitude'),
                    'longitude': online.get('longitude'),
                    'source': 'nominatim'
                }
            })

        return jsonify({
            'success': True,
            'data': {
                'original_text': text,
                'normalized_text': text,
                'source': 'local-fallback'
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# 司机推荐：供用户申请页按人数/目的地获取排序候选
def get_recommended_drivers():
    try:
        passenger_count = request.args.get('passenger_count', type=int) or 1
        destination = request.args.get('destination', type=str) or ''
        ranked = build_driver_recommendations(passenger_count=passenger_count, destination=destination)
        return jsonify({'success': True, 'data': ranked})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
