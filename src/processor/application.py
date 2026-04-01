import logging
import math
import time

from datetime import datetime, timedelta, timezone

from pydoover.processor.application import Application
from pydoover.models import MessageCreateEvent, AggregateUpdateEvent
from pydoover import ui, rpc

from .app_config import MaintenanceManagerConfig
from .app_tags import MaintenanceManagerTags
from .app_ui import MaintenanceManagerUI
from .models import ServiceLog

log = logging.getLogger(__name__)

DEFAULT_AVE_CALC_DAYS = 14


class MaintenanceManagerApplication(Application):
    config: MaintenanceManagerConfig
    tags: MaintenanceManagerTags

    config_cls = MaintenanceManagerConfig
    ui_cls = MaintenanceManagerUI
    tags_cls = MaintenanceManagerTags

    async def pre_hook_filter(self, event):
        if isinstance(event, MessageCreateEvent) and event.channel.name not in ("ui_cmds", "dv-rpc"):
            log.info(
                "Filtering event for channel that is not ui_cmds with a message create event."
            )
            return False

        if (
            isinstance(event, AggregateUpdateEvent)
            and event.channel.name != "tag_values"
        ):
            log.info(
                "Filtering event for channel that is not tag_values with an aggregate update event."
            )
            return False

        return True

    async def post_setup_filter(self, event):
        if (
            isinstance(event, AggregateUpdateEvent)
            and event.channel.name == "tag_values"
            and self.config.tracker_app_key.value not in event.request_data.data
        ):
            log.info(
                "Filtering event for tag_value that does not update the tracker app."
            )
            return False

        return True

    async def on_aggregate_update(self, event: AggregateUpdateEvent):
        # read tag values from the tracker app
        raw_run_hours = self.get_tracker_tag("run_hours", default=0)
        raw_odometer = self.get_tracker_tag("odometer_km", default=0)

        # ensure default tags exist on first run
        await self._ensure_defaults(raw_run_hours, raw_odometer)

        # apply offsets
        engine_hours = raw_run_hours + self.tags.hours_offset.value
        machine_odometer = raw_odometer + self.tags.odo_offset.value

        # compute average rates
        ave_rates = await self._get_average_rates(
            raw_run_hours,
            raw_odometer,
        )

        # read service parameters from tags (set by reset_service action)
        last_service_hours = self.tags.last_service_hours.value
        last_service_kms = self.tags.last_service_odometer.value
        last_service_date_ts = self.tags.last_service_date.value

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
        await self.tags.ave_hours_per_day.set(ave_rates["run_hours"])
        await self.tags.ave_kms_per_day.set(ave_rates["odometer"])

        # save all display values as tags
        await self.tags.next_service_est.set(
            int(next_service_est_dt.timestamp() * 1000)
            if next_service_est_dt is not None
            else None
        )
        await self.tags.days_till_next_service.set(
            int(days_till_service_due) if days_till_service_due is not None else None,
        )
        await self.tags.engine_hours.set(engine_hours)
        await self.tags.hours_till_next_service.set(hours_till_next_service)
        await self.tags.machine_odometer.set(machine_odometer)
        await self.tags.kms_till_next_service.set(kms_till_next_service)

        # check if we need to send a service-due notification
        await self._check_service_notification(days_till_service_due)

    # --- UI Callbacks ---

    @ui.handler("set_machine_hours", parser=int)
    async def on_set_hours(self, ctx, new_value: int):
        raw_run_hours = self.get_tracker_tag("run_hours")
        if raw_run_hours is None:
            log.info("Raw run hours is None.")
            return

        current_offset = self.tags.hours_offset.value
        current_display = raw_run_hours + current_offset
        new_offset = new_value - current_display + current_offset

        log.info(f"Setting machine hours to {new_value} (offset: {new_offset})")
        await self.tags.hours_offset.set(new_offset)
        # self.ui.set_hours.coerce(new_value)

    @ui.handler("set_odometer", parser=int)
    async def on_set_kms(self, ctx, new_value: int):
        raw_odometer = self.get_tracker_tag("odometer_km")
        if raw_odometer is None:
            raise ValueError("Raw odometer is None.")

        current_offset = self.tags.odo_offset.value
        current_display = raw_odometer + current_offset
        new_offset = new_value - current_display + current_offset

        log.info(f"Setting odometer to {new_value} (offset: {new_offset})")
        await self.tags.odo_offset.set(new_offset)
        # self.ui.set_kms.coerce(new_value)

    @rpc.handler("record_service", parser=ServiceLog.from_dict)
    async def on_record_service(self, ctx, payload: ServiceLog):
        """Record a service at the given datetime.

        If engine_hours or machine_odometer are not provided, fetch the
        closest historical values from before the service time.
        """
        # Fill in missing values from historical tag_values
        engine_hours = payload.engine_hours
        machine_odometer = payload.machine_odometer

        if payload.engine_hours is None or payload.machine_odometer is None:
            hist_hours, hist_odo = await self._get_historical_readings(
                payload.service_dt
            )
            if payload.engine_hours is None:
                engine_hours = hist_hours
            if payload.machine_odometer is None:
                machine_odometer = hist_odo

        log.info(
            f"Recording service: hours={engine_hours}, odo={machine_odometer}, date={payload.service_dt}"
        )
        await self.tags.last_service_date.set(payload.service_dt.timestamp() * 1000)
        await self.tags.service_notification_sent.set(False)
        if engine_hours is not None:
            await self.tags.last_service_hours.set(engine_hours)
        if machine_odometer is not None:
            await self.tags.last_service_odometer.set(machine_odometer)

    async def _get_historical_readings(self, before_dt):
        """Fetch engine hours and odometer from the tag_values message closest before before_dt."""
        tracker_key = self.config.tracker_app_key.value
        engine_hours = None
        machine_odometer = None

        try:
            messages = await self.api.list_messages(
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

                if raw_run_hours is not None:
                    engine_hours = raw_run_hours + self.tags.hours_offset.value
                if raw_odometer is not None:
                    machine_odometer = raw_odometer + self.tags.odo_offset.value

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

        if self.tags.service_notification_sent.value:
            return

        try:
            device_name = self.received_deployment_config["DEVICE_MAP"][
                str(self.agent_id)
            ]["display_name"]
        except (KeyError, TypeError):
            device_name = "Unknown device"

        message = (
            f"{device_name} is due for a service in {int(days_till_service_due)} days"
        )

        log.info(f"Sending service notification: {message}")
        await self.api.create_message(
            "notifications",
            {
                "severity": "warning",
                "topic": "service_due",
                "message": message,
            },
        )
        await self.tags.service_notification_sent.set(True)

    # --- Helper methods ---

    async def _ensure_defaults(self, raw_run_hours, raw_odometer):
        """Seed all tags with sensible defaults on first run."""
        now_ms = int(time.time() * 1000)

        if self.tags.last_service_date.value is None:
            await self.tags.last_service_date.set(now_ms)
        if self.tags.last_service_odometer.value is None:
            await self.tags.last_service_odometer.set(raw_odometer)
        if self.tags.last_service_hours.value is None:
            await self.tags.last_service_hours.set(raw_run_hours)

    def get_tracker_tag(self, key, default=None):
        return self.tag_manager.get_tag(key, default, self.config.tracker_app_key.value)

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
            messages = await self.api.list_messages(
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
