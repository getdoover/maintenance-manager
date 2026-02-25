from typing import Any

from pydoover.cloud.processor import run_app

from .application import MaintenanceManagerApplication
from .app_config import MaintenanceManagerConfig


def handler(event: dict[str, Any], context):
    """Lambda handler entry point."""
    MaintenanceManagerConfig.clear_elements()
    run_app(
        MaintenanceManagerApplication(config=MaintenanceManagerConfig()),
        event,
        context,
    )
