from pathlib import Path

from pydoover import config
from pydoover.processor import ExtendedPermissionsConfig, SubscriptionConfig


class MaintenanceDashboardConfig(config.Schema):
    subscription = SubscriptionConfig(default="deployment_config")
    extended_permissions = ExtendedPermissionsConfig()


def export():
    MaintenanceDashboardConfig.export(
        Path(__file__).parents[2] / "doover_config.json",
        "maintenance_dashboard",
    )
