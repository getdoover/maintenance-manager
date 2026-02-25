from pydoover.cloud.processor import run_app

from .application import MaintenanceDashboardApp
from .app_config import MaintenanceDashboardConfig


def handler(event, context):
    """Lambda handler entry point."""
    MaintenanceDashboardConfig.clear_elements()
    return run_app(
        MaintenanceDashboardApp(config=MaintenanceDashboardConfig()),
        event,
        context,
    )
