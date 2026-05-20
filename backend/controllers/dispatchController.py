"""调度控制器。"""

# 调度管理控制器
from flask import request, jsonify
from models.index import Dispatch, CarApplication, User, Vehicle
from services.dispatchService import create_dispatch as create_dispatch_service, start_dispatch as start_dispatch_service, cancel_dispatch as cancel_dispatch_service, DispatchServiceError
from controllers.controllerUtils import transactional_endpoint


# 获取所有调度
# 查询调度列表（可按状态筛选）
def get_dispatches():
    try:
        # 支持按状态筛选
        status = request.args.get('status')
        if status:
            dispatches = Dispatch.query.filter_by(status=status).all()
        else:
            dispatches = Dispatch.query.all()

        application_ids = [item.application_id for item in dispatches if item.application_id]
        driver_ids = [item.driver_id for item in dispatches if item.driver_id]
        vehicle_ids = [item.vehicle_id for item in dispatches if item.vehicle_id]

        applications = CarApplication.query.filter(CarApplication.id.in_(application_ids)).all() if application_ids else []
        drivers = User.query.filter(User.id.in_(driver_ids)).all() if driver_ids else []
        vehicles = Vehicle.query.filter(Vehicle.id.in_(vehicle_ids)).all() if vehicle_ids else []

        applicant_ids = [item.applicant_id for item in applications if item.applicant_id]
        applicants = User.query.filter(User.id.in_(applicant_ids)).all() if applicant_ids else []

        application_map = {item.id: item for item in applications}
        driver_map = {item.id: item for item in drivers}
        vehicle_map = {item.id: item for item in vehicles}
        applicant_map = {item.id: item for item in applicants}

        result = []
        for dispatch in dispatches:
            payload = dispatch.to_dict()
            application = application_map.get(dispatch.application_id)
            driver = driver_map.get(dispatch.driver_id)
            vehicle = vehicle_map.get(dispatch.vehicle_id)
            applicant = applicant_map.get(application.applicant_id) if application and application.applicant_id else None

            payload['applicant_name'] = applicant.name if applicant else None
            payload['driver_name'] = driver.name if driver else None
            payload['vehicle_plate_number'] = vehicle.plate_number if vehicle else None
            result.append(payload)

        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 创建调度（分配车辆和司机）
# 创建调度：校验申请、司机、车辆和时段冲突
@transactional_endpoint(DispatchServiceError)
def create_dispatch():
    data = request.json or {}
    dispatch = create_dispatch_service(data)
    return jsonify({'success': True, 'data': dispatch.to_dict()})


# 开始出车
# 将调度状态从 scheduled 推进到 in_progress
@transactional_endpoint(DispatchServiceError)
def start_dispatch(id):
    dispatch = start_dispatch_service(id)
    return jsonify({'success': True, 'data': dispatch.to_dict()})


# 取消调度
# 取消调度并回滚车辆/司机/申请状态
@transactional_endpoint(DispatchServiceError)
def cancel_dispatch(id):
    cancel_dispatch_service(id)
    return jsonify({'success': True, 'message': '调度已取消'})


