import logging
from datetime import datetime, timezone

from pydoover.processor import Application
from pydoover.models import (
    AggregateUpdateEvent,
    ConnectionStatus,
    ConnectionDetermination,
)

from .app_config import MaintenanceDashboardConfig
from .app_ui import MaintenanceDashboardUI

log = logging.getLogger(__name__)



class MaintenanceDashboardApp(Application):
    """
    Maintenance Dashboard Application.

    On deployment, the deployment_config aggregate is updated, which
    triggers on_aggregate_update via our subscription. We then push
    ui_state so the widget appears in the UI interpreter.
    """

    config: MaintenanceDashboardConfig
    config_cls = MaintenanceDashboardConfig
    ui_cls = MaintenanceDashboardUI

    async def on_aggregate_update(self, event: AggregateUpdateEvent):
        """Triggered when deployment_config aggregate is updated (i.e. on deployment)."""
        await self.api.ping_connection_at(
            datetime.now(timezone.utc),
            ConnectionStatus.continuous_online_no_ping,
            ConnectionDetermination.online,
            user_agent="maintenance-manager;dashboard-config",
            organisation_id=self.organisation_id,
        )
        log.info(f"Pinged connection for agent {self.agent_id}")
