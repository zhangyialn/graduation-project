"""审批流程控制器。"""

# 审批记录控制器
from flask import request, jsonify
from models.index import db, Approval, User, CarApplication
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from sqlalchemy.orm import aliased


# 兼容 Enum/字符串状态读取
def _enum_value(value):
    return value.value if hasattr(value, 'value') else value


# 获取所有审批记录

# 查询审批记录列表（可按状态筛选）
def get_approvals():
    try:
        # 支持按状态筛选
        status = request.args.get('status')
        if status:
            approvals = Approval.query.filter_by(status=status).all()
        else:
            approvals = Approval.query.all()
        return jsonify({'success': True, 'data': [approval.to_dict() for approval in approvals]})
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
        approvals = Approval.query.filter_by(application_id=application_id).all()
        return jsonify({'success': True, 'data': [approval.to_dict() for approval in approvals]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 获取某审批人的所有审批记录
# 查询某个审批人的审批记录
def get_approver_approvals(approver_id):
    try:
        approvals = Approval.query.filter_by(approver_id=approver_id).all()
        return jsonify({'success': True, 'data': [approval.to_dict() for approval in approvals]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 获取审批统计（按审批人统计）
# 审批统计：按审批人汇总总数/通过数/驳回数
def get_approval_statistics():
    try:
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

        rows = query.order_by(Approval.approved_at.desc(), Approval.id.desc()).all()

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

        return jsonify({'success': True, 'data': result})
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

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '审批提交成功',
            'data': {
                'application': application.to_dict(),
                'approval': approval.to_dict()
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
