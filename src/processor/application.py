import logging
import math
import time

from datetime import datetime, timedelta, timezone

from pydoover.cloud.processor.application import Application
from pydoover.cloud.processor.types import MessageCreateEvent
from pydoover import ui

from .app_config import MaintenanceManagerConfig
from .app_ui import MaintenanceManagerUI

log = logging.getLogger(__name__)

DEFAULT_AVE_CALC_DAYS = 14


class MaintenanceManagerApplication(Application):
    config: MaintenanceManagerConfig

    async def setup(self):
        self.ui = MaintenanceManagerUI(self.config, self.display_name, self.app_key)
        self.ui_manager.add_children(*self.ui.fetch())
        self.ui_manager.set_position(self.config.position.value)
        self.ui_manager.register_interactions(self)
        self.ui_manager.register_callbacks(self)

    async def on_message_create(self, event: MessageCreateEvent):
        if event.channel_name == "ui_cmds":
            msg_data = event.message.data or {}

            # Handle request-style messages (e.g. from dashboard)
            request = msg_data.get("request")
            if request and isinstance(request, dict):
                await self._handle_request(request)
            else:
                log.info(f"Handling ui_cmd: {msg_data}")
                await self.ui_manager.on_command_update_async(None, msg_data)
                await self.ui_manager.push_async(publish_fields=["currentValue"])

        # read tag values from the tracker app
        raw_run_hours = self.get_tracker_tag("run_hours", default=0)
        raw_odometer = self.get_tracker_tag("odometer_km", default=0)

        # ensure default tags exist on first run
        await self._ensure_defaults(raw_run_hours, raw_odometer)

        # apply offsets
        hours_offset = await self.get_tag("hours_offset")
        odo_offset = await self.get_tag("odo_offset")

        engine_hours = raw_run_hours + hours_offset
        machine_odometer = raw_odometer + odo_offset

        # compute average rates
        ave_rates = await self._get_average_rates(
            raw_run_hours,
            raw_odometer,
        )

        # read service parameters from tags (set by reset_service action)
        last_service_hours = await self.get_tag("last_service_hours")
        last_service_kms = await self.get_tag("last_service_kms")
        last_service_date_ts = await self.get_tag("last_service_date")

        try:
            last_service_date = datetime.fromtimestamp(
                last_service_date_ts / 1000, tz=timezone.utc
            )
        except (TypeError, ValueError, OSError):
            last_service_date = None

        # compute next service thresholds
        service_interval_hours = self.config.service_interval_hours.value
        service_interval_kms = self.config.service_interval_kms.value
        service_interval_months = self.config.service_interval_months.value

        next_service_hours = None
        if last_service_hours is not None and service_interval_hours is not None:
            next_service_hours = last_service_hours + service_interval_hours

        next_service_kms = None
        if last_service_kms is not None and service_interval_kms is not None:
            next_service_kms = last_service_kms + service_interval_kms

        next_service_date = None
        if last_service_date is not None and service_interval_months is not None:
            interval = math.ceil(service_interval_months)
            if interval > 0:
                try:
                    next_service_date = last_service_date + timedelta(
                        days=interval * 30
                    )
                except Exception as e:
                    log.error(f"Error calculating next service date: {e}")

        # compute remaining
        hours_till_next_service = None
        if next_service_hours is not None and engine_hours is not None:
            hours_till_next_service = next_service_hours - engine_hours

        kms_till_next_service = None
        if next_service_kms is not None and machine_odometer is not None:
            kms_till_next_service = next_service_kms - machine_odometer

        # compute next service estimate (earliest of date/hours/kms estimates)
        next_service_est_dt = self._get_next_service_estimate(
            engine_hours,
            machine_odometer,
            ave_rates and ave_rates["run_hours"],
            ave_rates and ave_rates["odometer"],
            next_service_hours,
            next_service_kms,
            next_service_date,
        )

        days_till_service_due = None
        if next_service_est_dt is not None:
            days_till_service_due = (
                next_service_est_dt - datetime.now(tz=timezone.utc)
            ).days

        # update UI
        self.ui.next_service_est.update(next_service_est_dt)
        self.ui.ave_hours_per_day.update(ave_rates["run_hours"])
        self.ui.ave_kms_per_day.update(ave_rates["odometer"])

        if days_till_service_due is not None:
            self.ui.days_till_next_service.update(int(days_till_service_due))
        else:
            self.ui.days_till_next_service.update(None)

        self.ui.engine_hours.update(engine_hours)
        self.ui.hours_till_next_service.update(hours_till_next_service)
        self.ui.machine_odometer.update(machine_odometer)
        self.ui.kms_till_next_service.update(kms_till_next_service)

        self.ui.last_service_date.update(last_service_date)
        self.ui.last_service_hours.update(last_service_hours)
        self.ui.last_service_kms.update(last_service_kms)

        # save all display values as tags
        await self.set_tag(
            "next_service_est",
            int(next_service_est_dt.timestamp() * 1000)
            if next_service_est_dt is not None
            else None,
        )
        await self.set_tag(
            "days_till_next_service",
            int(days_till_service_due) if days_till_service_due is not None else None,
        )
        await self.set_tag("engine_hours", engine_hours)
        await self.set_tag("hours_till_next_service", hours_till_next_service)
        await self.set_tag("machine_odometer", machine_odometer)
        await self.set_tag("kms_till_next_service", kms_till_next_service)

        # check if we need to send a service-due notification
        await self._check_service_notification(days_till_service_due)

        # push UI changes
        await self.ui_manager.push_async()

    # --- UI Callbacks ---

    @ui.callback("setHours")
    async def on_set_hours(self, element, new_value):
        if new_value is None:
            return

        raw_run_hours = self.get_tracker_tag("run_hours")
        if raw_run_hours is None:
            return

        current_offset = await self.get_tag("hours_offset", default=0) or 0
        current_display = raw_run_hours + current_offset
        new_offset = new_value - current_display + current_offset

        log.info(f"Setting machine hours to {new_value} (offset: {new_offset})")
        await self.set_tag("hours_offset", new_offset)
        self.ui.set_hours.coerce(new_value)

    @ui.callback("setKms")
    async def on_set_kms(self, element, new_value):
        if new_value is None:
            return

        raw_odometer = self.get_tracker_tag("odometer_km")
        if raw_odometer is None:
            return

        current_offset = await self.get_tag("odo_offset", default=0)
        current_display = raw_odometer + current_offset
        new_offset = new_value - current_display + current_offset

        log.info(f"Setting odometer to {new_value} (offset: {new_offset})")
        await self.set_tag("odo_offset", new_offset)
        self.ui.set_kms.coerce(new_value)

    @ui.callback("set_last_service_at")
    async def on_set_last_service_at(self, element, new_value):
        if new_value is None:
            return

        # new_value is an ISO datetime string or ms timestamp from the DateTimeParameter
        try:
            if isinstance(new_value, (int, float)):
                service_dt = datetime.fromtimestamp(new_value / 1000, tz=timezone.utc)
            else:
                service_dt = datetime.fromisoformat(str(new_value))
                if service_dt.tzinfo is None:
                    service_dt = service_dt.replace(tzinfo=timezone.utc)
        except (TypeError, ValueError) as e:
            log.warning(f"Invalid set_last_service_at value: {new_value} ({e})")
            return

        await self._record_service(service_dt)

    async def _handle_request(self, request):
        name = request.get("name")
        values = request.get("values", {})

        if name == "create_service":
            dt_ms = values.get("dt")
            if dt_ms is None:
                log.warning("create_service request missing 'dt'")
                return

            try:
                service_dt = datetime.fromtimestamp(dt_ms / 1000, tz=timezone.utc)
            except (TypeError, ValueError, OSError) as e:
                log.warning(f"Invalid create_service dt: {dt_ms} ({e})")
                return

            engine_hours = values.get("hours")
            machine_odometer = values.get("kms")
            await self._record_service(service_dt, engine_hours, machine_odometer)
        else:
            log.info(f"Unknown request: {name}")

    async def _record_service(self, service_dt, engine_hours=None, machine_odometer=None):
        """Record a service at the given datetime.

        If engine_hours or machine_odometer are not provided, fetch the
        closest historical values from before the service time.
        """
        service_date_ts = int(service_dt.timestamp() * 1000)

        # Fill in missing values from historical tag_values
        if engine_hours is None or machine_odometer is None:
            hist_hours, hist_odo = await self._get_historical_readings(service_dt)
            if engine_hours is None:
                engine_hours = hist_hours
            if machine_odometer is None:
                machine_odometer = hist_odo

        log.info(
            f"Recording service: hours={engine_hours}, odo={machine_odometer}, date={service_date_ts}"
        )
        await self.set_tag("last_service_date", service_date_ts)
        await self.set_tag("service_notification_sent", False)
        if engine_hours is not None:
            await self.set_tag("last_service_hours", engine_hours)
        if machine_odometer is not None:
            await self.set_tag("last_service_kms", machine_odometer)

    async def _get_historical_readings(self, before_dt):
        """Fetch engine hours and odometer from the tag_values message closest before before_dt."""
        tracker_key = self.config.tracker_app_key.value
        engine_hours = None
        machine_odometer = None

        try:
            messages = await self.api.get_channel_messages(
                agent_id=self.agent_id,
                channel_name="tag_values",
                before=before_dt,
                limit=1,
                field_names=[f"{tracker_key}.run_hours", f"{tracker_key}.odometer_km"],
            )

            if messages:
                msg = messages[0]
                msg_data = msg.data or {}
                tracker_data = msg_data.get(tracker_key, {})

                raw_run_hours = tracker_data.get("run_hours")
                raw_odometer = tracker_data.get("odometer_km")

                hours_offset = await self.get_tag("hours_offset", default=0) or 0
                odo_offset = await self.get_tag("odo_offset", default=0) or 0

                if raw_run_hours is not None:
                    engine_hours = raw_run_hours + hours_offset
                if raw_odometer is not None:
                    machine_odometer = raw_odometer + odo_offset

                log.info(
                    f"Found historical data at {msg.timestamp}: "
                    f"raw_hours={raw_run_hours}, raw_odo={raw_odometer}"
                )
            else:
                log.warning(f"No tag_values messages found before {before_dt}")
        except Exception as e:
            log.error(f"Error fetching historical tag_values: {e}")

        return engine_hours, machine_odometer

    # --- Notification methods ---

    async def _check_service_notification(self, days_till_service_due):
        alert_period = self.config.notification_alert_period.value
        if alert_period is None or days_till_service_due is None:
            return

        if days_till_service_due > alert_period:
            return

        already_sent = await self.get_tag("service_notification_sent", default=False)
        if already_sent:
            return

        try:
            device_name = self.received_deployment_config["DEVICE_MAP"][str(self.agent_id)]["display_name"]
        except (KeyError, TypeError):
            device_name = "Unknown device"

        message = f"{device_name} is due for a service in {int(days_till_service_due)} days"

        log.info(f"Sending service notification: {message}")
        await self.api.publish_message(
            self.agent_id,
            "notifications",
            {
                "severity": "warning",
                "topic": "service_due",
                "message": message,
            },
        )
        await self.set_tag("service_notification_sent", True)

    # --- Helper methods ---

    async def _ensure_defaults(self, raw_run_hours, raw_odometer):
        """Seed all tags with sensible defaults on first run."""
        now_ms = int(time.time() * 1000)

        defaults = {
            "hours_offset": 0,
            "odo_offset": 0,
            "last_service_date": now_ms,
            "last_service_hours": raw_run_hours,
            "last_service_kms": raw_odometer,
        }

        for key, default in defaults.items():
            existing = await self.get_tag(key)
            if existing is None and default is not None:
                await self.set_tag(key, default)

    def get_tracker_tag(self, key, default=None):
        try:
            return self._tag_values[self.config.tracker_app_key.value][key]
        except (KeyError, TypeError):
            return default

    def _get_next_service_estimate(
        self,
        curr_hours,
        curr_odo,
        ave_hours_per_day,
        ave_kms_per_day,
        next_service_hours,
        next_service_kms,
        next_service_date,
    ):
        estimates = []
        now = datetime.now(tz=timezone.utc)

        if (
            curr_hours is not None
            and ave_hours_per_day is not None
            and ave_hours_per_day > 0
            and next_service_hours is not None
        ):
            hours_remaining = next_service_hours - curr_hours
            days_remaining = hours_remaining / ave_hours_per_day
            estimates.append(now + timedelta(days=days_remaining))

        if (
            curr_odo is not None
            and ave_kms_per_day is not None
            and ave_kms_per_day > 0
            and next_service_kms is not None
        ):
            kms_remaining = next_service_kms - curr_odo
            days_remaining = kms_remaining / ave_kms_per_day
            estimates.append(now + timedelta(days=days_remaining))

        if next_service_date is not None:
            estimates.append(next_service_date)

        if estimates:
            return min(estimates)
        return None

    async def _get_average_rates(self, raw_run_hours, raw_odometer):
        tracker_key = self.config.tracker_app_key.value
        start_date = datetime.now(tz=timezone.utc) - timedelta(
            days=self.config.average_use_period.value
        )

        hours_per_day = 0
        kms_per_day = 0

        try:
            messages = await self.api.get_channel_messages(
                agent_id=self.agent_id,
                channel_name="tag_values",
                after=start_date,
                # before=datetime.now(tz=timezone.utc),
                limit=1,
                field_names=[f"{tracker_key}.run_hours", f"{tracker_key}.odometer_km"],
            )
        except Exception as e:
            log.error(f"Error fetching tag_values messages: {e}")
            return None

        if not messages:
            return None

        msg = messages[0]
        msg_data = msg.data or {}
        tracker_data = msg_data.get(tracker_key, {})

        old_hours = tracker_data.get("run_hours")
        old_odo = tracker_data.get("odometer_km")

        elapsed = datetime.now(tz=timezone.utc) - msg.timestamp

        log.info(
            f"Early data: {tracker_data}. Current data: ({raw_run_hours, raw_odometer}). Elapsed: {elapsed}"
        )

        if old_hours is not None and raw_run_hours is not None:
            hours_per_day = (
                (raw_run_hours - old_hours) / elapsed.total_seconds() * (24 * 60 * 60)
            )

        if old_odo is not None and raw_odometer is not None:
            kms_per_day = (
                (raw_odometer - old_odo) / elapsed.total_seconds() * (24 * 60 * 60)
            )

        return {
            "run_hours": hours_per_day,
            "odometer": kms_per_day,
        }
