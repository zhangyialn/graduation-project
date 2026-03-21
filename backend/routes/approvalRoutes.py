# 审批相关路由
from flask import Blueprint
from controllers.approvalController import get_approvals, get_approval, get_application_approvals, get_approver_approvals, get_approval_statistics
from middleware.auth_middleware import jwt_required

approvalBlueprint = Blueprint('approval', __name__, url_prefix='/api/approvals')

# 注册路由
approvalBlueprint.route('', methods=['GET'])(jwt_required()(get_approvals))
approvalBlueprint.route('/<int:id>', methods=['GET'])(jwt_required()(get_approval))
approvalBlueprint.route('/application/<int:application_id>', methods=['GET'])(jwt_required()(get_application_approvals))
approvalBlueprint.route('/approver/<int:approver_id>', methods=['GET'])(jwt_required()(get_approver_approvals))
approvalBlueprint.route('/statistics', methods=['GET'])(jwt_required()(get_approval_statistics))