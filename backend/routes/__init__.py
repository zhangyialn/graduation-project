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

__all__ = ['userBlueprint', 'vehicleBlueprint', 'applicationBlueprint', 'approvalBlueprint', 'dispatchBlueprint', 'tripBlueprint', 'driverBlueprint', 'reportBlueprint', 'authBlueprint']