"""路由蓝图统一导出入口。"""

# routes 包初始化
from .userRoutes import userBlueprint
from .vehicleRoutes import vehicleBlueprint
from .applicationRoutes import applicationBlueprint
from .approvalRoutes import approvalBlueprint
from .dispatchRoutes import dispatchBlueprint
from .tripRoutes import tripBlueprint
from .driverRoutes import driverBlueprint
from .reportRoutes import reportBlueprint
from .authRoutes import authBlueprint
from .translateRoutes import translateBlueprint

__all__ = ['userBlueprint', 'vehicleBlueprint', 'applicationBlueprint', 'approvalBlueprint', 'dispatchBlueprint', 'tripBlueprint', 'driverBlueprint', 'reportBlueprint', 'authBlueprint', 'translateBlueprint']
