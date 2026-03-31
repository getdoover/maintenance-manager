from pathlib import Path

from pydoover import ui


class MaintenanceDashboardUI(ui.UI, default_open=True):
    widget = ui.RemoteComponent(
        name="MaintenanceDashboard",
        display_name="MaintenanceDashboard",
        component_url="$config.app().dv_widget_url",
        scope="MaintenanceDashboardWidget",
        module="./MaintenanceDashboardWidget",
        app_key="$config.app().APP_KEY",
        manager_app_key="maintenance_manager_1",
    )


def export():
    MaintenanceDashboardUI(None, None, None).export(
        Path(__file__).parents[2] / "doover_config.json", "maintenance_dashboard"
    )
