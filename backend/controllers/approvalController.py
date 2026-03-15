# 审批记录控制器
from flask import request, jsonify
from models.index import db, Approval, User, CarApplication


# 获取所有审批记录
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
def get_approval(id):
    try:
        approval = Approval.query.get(id)
        if not approval:
            return jsonify({'success': False, 'message': '审批记录不存在'})
        return jsonify({'success': True, 'data': approval.to_dict()})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 获取某申请的所有审批记录
def get_application_approvals(application_id):
    try:
        approvals = Approval.query.filter_by(application_id=application_id).all()
        return jsonify({'success': True, 'data': [approval.to_dict() for approval in approvals]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 获取某审批人的所有审批记录
def get_approver_approvals(approver_id):
    try:
        approvals = Approval.query.filter_by(approver_id=approver_id).all()
        return jsonify({'success': True, 'data': [approval.to_dict() for approval in approvals]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# 获取审批统计（按审批人统计）
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