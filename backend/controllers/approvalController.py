"""审批流程控制器。"""

# 审批记录控制器
from flask import request, jsonify
from models.index import db, Approval, User, CarApplication, Dispatch, Vehicle, RoleEnum
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from sqlalchemy.orm import aliased


# 兼容 Enum/字符串状态读取
def _enum_value(value):
    return value.value if hasattr(value, 'value') else value


# 解析可选分页参数：有参数走分页，无参数保持历史全量返回。
def _parse_optional_pagination(default_limit=20, max_limit=100):
    # 仅当前端显式传参时才启用分页，默认保持历史全量返回。
    has_pagination = ('page' in request.args) or ('limit' in request.args)
    if not has_pagination:
        return None, None, False

    page = request.args.get('page', default=1, type=int) or 1
    limit = request.args.get('limit', default=default_limit, type=int) or default_limit
    page = max(page, 1)
    limit = min(max(limit, 1), max_limit)
    return page, limit, True


# 组装统一分页响应结构，减少前端各页面解析差异。
def _pagination_meta(total, page, limit):
    # 统一分页响应结构，避免各审批接口字段命名不一致。
    pages = (total + limit - 1) // limit if limit else 0
    return {
        'total': total,
        'page': page,
        'limit': limit,
        'pages': pages,
        'has_next': page < pages,
        'has_prev': page > 1
    }


# 获取所有审批记录

# 查询审批记录列表（可按状态筛选）
def get_approvals():
    try:
        page, limit, should_paginate = _parse_optional_pagination()
        # 支持按状态筛选
        status = request.args.get('status')
        query = Approval.query
        if status:
            query = query.filter_by(status=status)

        if not should_paginate:
            approvals = query.all()
            return jsonify({'success': True, 'data': [approval.to_dict() for approval in approvals]})

        # 审批记录按最新ID倒序展示，符合“先处理新单”的业务习惯。
        total = query.count()
        approvals = query.order_by(Approval.id.desc()).offset((page - 1) * limit).limit(limit).all()
        return jsonify({
            'success': True,
            'data': [approval.to_dict() for approval in approvals],
            'pagination': _pagination_meta(total, page, limit)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 获取单个审批记录
# 查询单条审批记录
def get_approval(id):
    try:
        approval = Approval.query.get(id)
        if not approval:
            return jsonify({'success': False, 'message': '审批记录不存在'})
        return jsonify({'success': True, 'data': approval.to_dict()})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 获取某申请的所有审批记录
# 查询某个申请对应的全部审批记录
def get_application_approvals(application_id):
    try:
        page, limit, should_paginate = _parse_optional_pagination()
        query = Approval.query.filter_by(application_id=application_id)

        if not should_paginate:
            approvals = query.all()
            return jsonify({'success': True, 'data': [approval.to_dict() for approval in approvals]})

        total = query.count()
        approvals = query.order_by(Approval.id.desc()).offset((page - 1) * limit).limit(limit).all()
        return jsonify({
            'success': True,
            'data': [approval.to_dict() for approval in approvals],
            'pagination': _pagination_meta(total, page, limit)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 获取某审批人的所有审批记录
# 查询某个审批人的审批记录
def get_approver_approvals(approver_id):
    try:
        page, limit, should_paginate = _parse_optional_pagination()
        query = Approval.query.filter_by(approver_id=approver_id)

        if not should_paginate:
            approvals = query.all()
            return jsonify({'success': True, 'data': [approval.to_dict() for approval in approvals]})

        total = query.count()
        approvals = query.order_by(Approval.id.desc()).offset((page - 1) * limit).limit(limit).all()
        return jsonify({
            'success': True,
            'data': [approval.to_dict() for approval in approvals],
            'pagination': _pagination_meta(total, page, limit)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 获取审批统计（按审批人统计）
# 审批统计：按审批人汇总总数/通过数/驳回数
def get_approval_statistics():
    try:
        page, limit, should_paginate = _parse_optional_pagination()
        department_id = request.args.get('department_id', type=int)
        applicant_user = aliased(User)
        approver_user = aliased(User)

        query = db.session.query(
            Approval,
            CarApplication,
            applicant_user.name.label('applicant_name'),
            approver_user.name.label('approver_name')
        ).join(
            CarApplication, Approval.application_id == CarApplication.id
        ).outerjoin(
            applicant_user, CarApplication.applicant_id == applicant_user.id
        ).outerjoin(
            approver_user, Approval.approver_id == approver_user.id
        )

        if department_id:
            query = query.filter(CarApplication.department_id == department_id)

        ordered_query = query.order_by(Approval.approved_at.desc(), Approval.id.desc())
        if should_paginate:
            # 统计列表分页时仍按审批时间倒序，保证列表语义稳定。
            total = query.count()
            rows = ordered_query.offset((page - 1) * limit).limit(limit).all()
        else:
            rows = ordered_query.all()

        result = []
        for approval, application, applicant_name, approver_name in rows:
            result.append({
                'approval_id': approval.id,
                'application_id': approval.application_id,
                'approval_status': _enum_value(approval.status),
                'approver_id': approval.approver_id,
                'approver_name': approver_name or '未知审批人',
                'applicant_name': applicant_name or '未知申请人',
                'purpose': application.purpose,
                'start_point': application.start_point,
                'destination': application.destination,
                'start_time': application.start_time.isoformat() if application.start_time else None,
                'application_time': application.created_at.isoformat() if application.created_at else None,
                'approval_time': approval.approved_at.isoformat() if approval.approved_at else None
            })

        payload = {'success': True, 'data': result}
        if should_paginate:
            payload['pagination'] = _pagination_meta(total, page, limit)
        return jsonify(payload)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 提交审批结果（同意/驳回）
# 提交审批结果并同步更新申请状态
def submit_approval(application_id):
    try:
        data = request.json or {}
        status = data.get('status')
        comment = data.get('comment')
        start_point = data.get('start_point')

        if status not in ['approved', 'rejected']:
            return jsonify({'success': False, 'message': '审批状态必须为 approved 或 rejected'}), 400

        application = CarApplication.query.get(application_id)
        if not application:
            return jsonify({'success': False, 'message': '申请不存在'}), 404

        if _enum_value(application.status) != 'pending':
            return jsonify({'success': False, 'message': '仅待审批申请可提交审批结果'}), 400

        current_user_id = get_jwt_identity()
        approval_time = datetime.utcnow()

        approval = Approval(
            application_id=application_id,
            approver_id=current_user_id,
            status=status,
            comment=comment,
            approved_at=approval_time
        )
        db.session.add(approval)

        application.status = status
        application.approval_comment = comment
        if start_point is not None:
            application.start_point = start_point
        application.approved_by = current_user_id
        application.approved_at = approval_time

        auto_dispatch = None
        if status == 'approved':
            driver = User.query.filter_by(id=application.driver_id, role=RoleEnum.driver, is_deleted=False).first()
            vehicle = Vehicle.query.get(driver.vehicle_id) if driver and driver.vehicle_id else None

            can_auto_dispatch = (
                driver
                and vehicle
                and not vehicle.is_deleted
                and _enum_value(driver.driver_status) == 'available'
                and _enum_value(vehicle.status) == 'available'
            )

            if can_auto_dispatch:
                existing_dispatch = Dispatch.query.filter(
                    Dispatch.application_id == application.id,
                    Dispatch.status.in_(['scheduled', 'in_progress'])
                ).first()

                if existing_dispatch:
                    auto_dispatch = existing_dispatch
                else:
                    auto_dispatch = Dispatch(
                        application_id=application.id,
                        vehicle_id=vehicle.id,
                        driver_id=driver.id,
                        dispatcher_id=current_user_id,
                        status='scheduled'
                    )
                    db.session.add(auto_dispatch)

                application.status = 'dispatched'
                driver.driver_status = 'busy'
                vehicle.status = 'in_use'

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '审批提交成功',
            'data': {
                'application': application.to_dict(),
                'approval': approval.to_dict(),
                'auto_dispatch': auto_dispatch.to_dict() if auto_dispatch else None
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
