from pathlib import Path

from pydoover import ui
from pydoover.ui import RemoteComponent

from processor.app_tags import MaintenanceManagerTags

WIDGET_URL = (
    "https://getdoover.github.io/maintenance-manager/MaintenanceDashboardWidget.js"
)


class MaintenanceManagerUI(ui.UI):
    tabs = ui.TabContainer(
        name="tabs",
        display_name="Tabs",
        children=[
            ui.Container(
                "Service Info",
                children=[
                    ui.Timestamp(
                        "Next Service Estimate",
                        icon="calendar-day",
                        value=MaintenanceManagerTags.next_service_est,
                    ),
                    ui.NumericVariable(
                        "Kms Till Next Service",
                        precision=1,
                        units="km",
                        icon="road",
                        # hidden=config.service_interval_kms.value is not None,
                        value=MaintenanceManagerTags.kms_till_next_service,
                    ),
                    ui.NumericVariable(
                        "Hours To Next Service",
                        precision=1,
                        units="hrs",
                        icon="clock",
                        # hidden=config.service_interval_hours.value is not None,
                        value=MaintenanceManagerTags.hours_till_next_service,
                    ),
                    ui.NumericVariable(
                        "Days To Next Service",
                        precision=0,
                        units="days",
                        icon="calendar",
                        value=MaintenanceManagerTags.days_till_next_service,
                    ),
                ],
            ),
            ui.Container(
                "Usage Info",
                children=[
                    ui.NumericVariable(
                        "Ave Hours Per Day",
                        precision=1,
                        units="hrs",
                        icon="clock",
                        value=MaintenanceManagerTags.ave_hours_per_day,
                    ),
                    ui.NumericVariable(
                        "Ave Kms Per Day",
                        precision=1,
                        units="km",
                        icon="road",
                        value=MaintenanceManagerTags.ave_kms_per_day,
                    ),
                    ui.NumericVariable(
                        "Engine Hours",
                        precision=1,
                        units="hrs",
                        icon="hourglass",
                        value=MaintenanceManagerTags.engine_hours,
                    ),
                    ui.NumericVariable(
                        "Odometer",
                        precision=1,
                        units="km",
                        icon="gauge",
                        value=MaintenanceManagerTags.machine_odometer,
                    ),
                ],
            ),
            ui.Container(
                "Last Service",
                children=[
                    ui.Timestamp(
                        "Last Service Date",
                        icon="calendar-day",
                        value=MaintenanceManagerTags.last_service_date,
                    ),
                    ui.NumericVariable(
                        "Last Service Hours",
                        precision=1,
                        units="hrs",
                        icon="clock",
                        value=MaintenanceManagerTags.last_service_hours,
                    ),
                    ui.NumericVariable(
                        "Last Service Odometer",
                        precision=1,
                        units="km",
                        icon="road",
                        value=MaintenanceManagerTags.last_service_odometer,
                    ),
                ],
            ),
        ],
    )

    # --- Config submodule ---
    config_submodule = ui.Submodule(
        "Config",
        icon="gear",
        children=[
            ui.FloatInput(
                "Set Machine Hours",
                units="hrs",
                icon="clock",
                requires_confirm=True,
            ),
            ui.FloatInput(
                "Set Odometer",
                units="km",
                icon="road",
                requires_confirm=True,
            ),
            RemoteComponent(
                name="LogServiceWidget",
                display_name="Log Service",
                component_url="$config.app().dv_widget_url",
                scope="MaintenanceDashboard",
                module="./LogServiceWidget",
                device_name="$config.app().DISPLAY_NAME",
                app_key="$config.app().APP_KEY",
            ),
        ],
    )

def export():
    MaintenanceManagerUI(None, None, None).export(
        Path(__file__).parents[2] / "doover_config.json", "maintenance_manager"
    )
