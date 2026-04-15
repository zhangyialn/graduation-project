"""调度控制器。"""

# 调度管理控制器
from flask import request, jsonify
from models.index import Dispatch
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
        return jsonify({'success': True, 'data': [dispatch.to_dict() for dispatch in dispatches]})
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


