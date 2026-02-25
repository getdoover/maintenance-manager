from pathlib import Path

from pydoover import config
from pydoover.cloud.processor import ExtendedPermissionsConfig, SubscriptionConfig, ScheduleConfig


class MaintenanceDashboardConfig(config.Schema):
    def __init__(self):
        self.subscription = SubscriptionConfig(default="deployment_config")
        self.extended_permissions = ExtendedPermissionsConfig()


def export():
    MaintenanceDashboardConfig().export(
        Path(__file__).parents[2] / "doover_config.json",
        "maintenance_dashboard",
    )


if __name__ == "__main__":
    export()
