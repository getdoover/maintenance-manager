from pydoover import ui


class MaintenanceManagerUI:
    def __init__(self):
        self.next_service_est = ui.TextVariable(
            "nextServiceEst",
            "Next Service Estimate",
        )

        self.ave_hours_per_day = ui.NumericVariable(
            "aveHoursPerDay",
            "Ave Hours Per Day",
            precision=1,
            units="hrs"
        )
        self.ave_kms_per_day = ui.NumericVariable(
            "aveKmsPerDay",
            "Ave Kms Per Day",
            precision=1,
            units="km"
        )

        # --- Config submodule ---
        self.config_submodule = ui.Submodule("config_submodule", "Config")
        self.ave_calc_days = ui.NumericParameter(
            "aveCalcDays",
            "Ave Use Calculation",
            units="days",
        )
        self.set_hours = ui.NumericParameter(
            "setHours",
            "Set Machine Hours",
            units="hrs",
        )
        self.set_kms = ui.NumericParameter(
            "setKms",
            "Set Odometer",
            units="km",
        )
        self.config_submodule.add_children(
            self.set_hours,
            self.set_kms,
            self.ave_calc_days,
        )

        # next bank of variables
        self.days_till_next_service = ui.NumericVariable(
            "daysTillNextService",
            "Days To Next Service",
            precision=0,
            units="days"
        )

        self.engine_hours = ui.NumericVariable(
            "engineHours",
            "Engine Hours",
            precision=1,
            units="hrs",
        )
        self.hours_till_next_service = ui.NumericVariable(
            "hoursTillNextService",
            "Hours To Next Service",
            precision=1,
            units="hrs",
        )

        self.machine_odometer = ui.NumericVariable(
            "machineOdometer",
            "Odometer",
            precision=1,
            units="km"
        )
        self.kms_till_next_service = ui.NumericVariable(
            "kmsTillNextService",
            "Kms Till Next Service",
            precision=1,
            units="km"
        )
        self.reset_service = ui.Action("reset_service", "Set Service Now", requires_confirm=True)

    def fetch(self):
        return (
            self.next_service_est,
            self.ave_hours_per_day,
            self.ave_kms_per_day,
            self.config_submodule,
            self.days_till_next_service,
            self.engine_hours,
            self.hours_till_next_service,
            self.machine_odometer,
            self.kms_till_next_service,
        )
