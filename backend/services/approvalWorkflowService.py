"""审批工作流服务。"""

from datetime import datetime
from models.index import Approval, CarApplication, Dispatch, User, Vehicle, RoleEnum
from controllers.commonHelpers import enum_value, normalize_identity


class ApprovalWorkflowError(Exception):
    """审批工作流异常，包含可直接返回给接口层的状态码。"""

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def submit_approval_workflow(application_id, current_user_id, payload):
    """处理审批结果提交与自动调度联动，不负责 commit/rollback。"""
    status = payload.get('status')
    comment = payload.get('comment')
    start_point = payload.get('start_point')

    if status not in ['approved', 'rejected']:
        raise ApprovalWorkflowError('审批状态必须为 approved 或 rejected', 400)

    application = CarApplication.query.get(application_id)
    if not application:
        raise ApprovalWorkflowError('申请不存在', 404)

    if enum_value(application.status) != 'pending':
        raise ApprovalWorkflowError('仅待审批申请可提交审批结果', 400)

    applicant_id = normalize_identity(application.applicant_id)
    if applicant_id is not None and normalize_identity(current_user_id) == applicant_id:
        raise ApprovalWorkflowError('不能审批自己提交的申请', 403)

    approval_time = datetime.utcnow()
    approval = Approval(
        application_id=application_id,
        approver_id=current_user_id,
        status=status,
        comment=comment,
        approved_at=approval_time
    )

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
            and enum_value(driver.driver_status) == 'available'
            and enum_value(vehicle.status) == 'available'
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

            application.status = 'dispatched'
            driver.driver_status = 'busy'
            vehicle.status = 'in_use'

    return {
        'application': application,
        'approval': approval,
        'auto_dispatch': auto_dispatch
    }
