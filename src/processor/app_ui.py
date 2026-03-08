from pydoover import ui
from pydoover.ui import RemoteComponent

from .app_config import MaintenanceManagerConfig

WIDGET_URL = (
    "https://getdoover.github.io/maintenance-manager/MaintenanceDashboardWidget.js"
)


class MaintenanceManagerUI:
    def __init__(
        self, config: MaintenanceManagerConfig, device_name: str, app_key: str
    ):
        self.next_service_est = ui.Timestamp(
            "nextServiceEst",
            "Next Service Estimate",
            icon="calendar-day",
        )
        self.days_till_next_service = ui.NumericVariable(
            "daysTillNextService",
            "Days To Next Service",
            precision=0,
            units="days",
            icon="calendar",
        )
        self.hours_till_next_service = ui.NumericVariable(
            "hoursTillNextService",
            "Hours To Next Service",
            precision=1,
            units="hrs",
            icon="clock",
            hidden=config.service_interval_hours.value is not None,
        )
        self.kms_till_next_service = ui.NumericVariable(
            "kmsTillNextService",
            "Kms Till Next Service",
            precision=1,
            units="km",
            icon="road",
            hidden=config.service_interval_kms.value is not None,
        )

        self.ave_hours_per_day = ui.NumericVariable(
            "aveHoursPerDay",
            "Ave Hours Per Day",
            precision=1,
            units="hrs",
            icon="clock",
        )
        self.ave_kms_per_day = ui.NumericVariable(
            "aveKmsPerDay",
            "Ave Kms Per Day",
            precision=1,
            units="km",
            icon="road",
        )

        # next bank of variables
        self.engine_hours = ui.NumericVariable(
            "engineHours",
            "Engine Hours",
            precision=1,
            units="hrs",
            icon="hourglass",
        )
        self.machine_odometer = ui.NumericVariable(
            "machineOdometer", "Odometer", precision=1, units="km", icon="gauge"
        )

        service_info = ui.Container(
            "service_info",
            "Service Info",
            children=[
                self.next_service_est,
                self.kms_till_next_service,
                self.hours_till_next_service,
                self.days_till_next_service,
            ],
        )

        engine_info = ui.Container(
            "engine_info",
            "Usage Info",
            children=[
                self.ave_hours_per_day,
                self.ave_kms_per_day,
                self.engine_hours,
                self.machine_odometer,
            ],
        )

        self.last_service_date = ui.Timestamp(
            "lastServiceDate",
            "Last Service Date",
            icon="calendar-day",
        )
        self.last_service_hours = ui.NumericVariable(
            "lastServiceHours",
            "Last Service Hours",
            precision=1,
            units="hrs",
            icon="clock",
        )
        self.last_service_kms = ui.NumericVariable(
            "lastServiceKms",
            "Last Service Odometer",
            precision=1,
            units="km",
            icon="road",
        )
        last_service_info = ui.Container(
            "last_service_info",
            "Last Service",
            children=[
                self.last_service_date,
                self.last_service_hours,
                self.last_service_kms,
            ],
        )

        self.tabs = ui.TabContainer(
            name="tabs",
            display_name="Tabs",
            children=[service_info, engine_info, last_service_info],
        )

        # --- Config submodule ---
        self.config_submodule = ui.Submodule("config_submodule", "Config", icon="gear")
        self.set_hours = ui.NumericParameter(
            "setHours",
            "Set Machine Hours",
            units="hrs",
            icon="clock",
            requires_confirm=True,
        )
        self.set_kms = ui.NumericParameter(
            "setKms",
            "Set Odometer",
            units="km",
            icon="road",
            requires_confirm=True,
        )
        self.log_service_widget = RemoteComponent(
            name="LogServiceWidget",
            display_name="Log Service",
            component_url=WIDGET_URL,
            module="./LogServiceWidget",
            device_name=device_name,
            app_key=app_key,
        )
        self.config_submodule.add_children(
            self.set_hours, self.set_kms, self.log_service_widget
        )

    def fetch(self):
        return (
            self.tabs,
            self.config_submodule,
        )
