"""审批流程控制器。"""

# 审批记录控制器
from flask import request, jsonify
from models.index import db, Approval, User, CarApplication
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime


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
        from sqlalchemy import func
        
        stats = db.session.query(
            Approval.approver_id,
            func.count(Approval.id).label('total_count'),
            func.sum(func.if_(Approval.status == 'approved', 1, 0)).label('approved_count'),
            func.sum(func.if_(Approval.status == 'rejected', 1, 0)).label('rejected_count')
        ).group_by(Approval.approver_id).all()
        
        result = []
        for stat in stats:
            approver = User.query.get(stat.approver_id)
            result.append({
                'approver_id': stat.approver_id,
                'approver_name': approver.name if approver else '未知用户',
                'total_count': stat.total_count,
                'approved_count': stat.approved_count,
                'rejected_count': stat.rejected_count
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

        approval = Approval(
            application_id=application_id,
            approver_id=current_user_id,
            status=status,
            comment=comment
        )
        db.session.add(approval)

        application.status = status
        application.approval_comment = comment
        if start_point is not None:
            application.start_point = start_point
        application.approved_by = current_user_id
        application.approved_at = datetime.utcnow()

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
