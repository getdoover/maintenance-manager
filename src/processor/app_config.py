from pathlib import Path

from pydoover import config
from pydoover.cloud.processor import ManySubscriptionConfig


class MaintenanceManagerConfig(config.Schema):
    def __init__(self):
        self.subscription = ManySubscriptionConfig()
        self.position = config.ApplicationPosition()
        self.tracker_app_key = config.ApplicationInstall(
            "Tracker App Key",
            description="The app key for the tracker application that provides tag values",
        )

        self.service_interval_hours = config.Number(
            "Service Interval (hours)",
            description="The target number of engine hours between services",
            exclusive_minimum=0,
            default=None,
        )
        self.service_interval_kms = config.Number(
            "Service Interval (kms)",
            description="The target number of kms between services",
            exclusive_minimum=0,
            default=None,
        )
        self.service_interval_months = config.Number(
            "Service Interval (months)",
            description="The target number of months between services",
            exclusive_minimum=0,
            default=None,
        )


def export():
    MaintenanceManagerConfig().export(
        Path(__file__).parents[2] / "doover_config.json", "maintenance_manager"
    )


if __name__ == "__main__":
    export()
