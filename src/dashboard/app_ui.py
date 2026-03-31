from pathlib import Path

from pydoover import ui


class MaintenanceDashboardUI(ui.UI, default_open=True):
    widget = ui.RemoteComponent(
        name="MaintenanceDashboard",
        display_name="MaintenanceDashboard",
        component_url="https://getdoover.github.io/maintenance-manager/MaintenanceDashboardWidget.js",
        app_key="$config.app().APP_KEY",
        manager_app_key="maintenance_manager_1",
    )


def export():
    MaintenanceDashboardUI(None, None).export(
        Path(__file__).parents[2] / "doover_config.json", "maintenance_manager"
    )
