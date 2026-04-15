"""审批流程控制器。"""

# 审批记录控制器
from flask import request, jsonify
from models.index import db, Approval, User, CarApplication
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.orm import aliased
from controllers.common_helpers import enum_value as _enum_value, normalize_identity as _normalize_identity, parse_optional_pagination as _parse_optional_pagination, pagination_meta as _pagination_meta
from services.approval_workflow_service import submit_approval_workflow, ApprovalWorkflowError
from controllers.controller_utils import transactional_endpoint


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
@transactional_endpoint(ApprovalWorkflowError)
def submit_approval(application_id):
    data = request.json or {}
    current_user_id = _normalize_identity(get_jwt_identity())
    workflow_result = submit_approval_workflow(application_id, current_user_id, data)
    application = workflow_result['application']
    approval = workflow_result['approval']
    auto_dispatch = workflow_result['auto_dispatch']

    db.session.add(approval)

    return jsonify({
        'success': True,
        'message': '审批提交成功',
        'data': {
            'application': application.to_dict(),
            'approval': approval.to_dict(),
            'auto_dispatch': auto_dispatch.to_dict() if auto_dispatch else None
        }
    })
