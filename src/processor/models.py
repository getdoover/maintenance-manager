from datetime import datetime, timezone
from typing import Any


class ServiceLog:
    def __init__(self, service_dt: datetime, engine_hours: float, machine_odometer: float):
        self.service_dt = service_dt
        self.engine_hours = engine_hours
        self.machine_odometer = machine_odometer

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            datetime.fromtimestamp(data["service_dt"] / 1000.0, tz=timezone.utc),
            data["engine_hours"],
            data["machine_odometer"],
        )
