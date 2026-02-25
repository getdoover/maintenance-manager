import logging

from pydoover.cloud.processor import Application
from pydoover.cloud.processor.types import AggregateUpdateEvent
from pydoover.ui import RemoteComponent

from .app_config import MaintenanceDashboardConfig

log = logging.getLogger(__name__)

WIDGET_NAME = "MaintenanceDashboard"
FILE_CHANNEL = "maintenance_dashboard_widget"


class MaintenanceDashboardApp(Application):
    """
    Maintenance Dashboard Application.

    On deployment, the deployment_config aggregate is updated, which
    triggers on_aggregate_update via our subscription. We then push
    ui_state so the widget appears in the UI interpreter.
    """

    config: MaintenanceDashboardConfig

    async def setup(self):
        """Called once before processing any event."""
        self.ui_manager.set_children([
            RemoteComponent(
                name=WIDGET_NAME,
                display_name=WIDGET_NAME,
                component_url=FILE_CHANNEL,
            ),
        ])

    async def on_aggregate_update(self, event: AggregateUpdateEvent):
        """Triggered when deployment_config aggregate is updated (i.e. on deployment)."""
        log.info(f"Aggregate update received for agent {self.agent_id}")
        await self.ui_manager.push_async(even_if_empty=True)

        # Patch defaultOpen onto our application so the widget is
        # expanded on page load instead of collapsed.
        await self.api.update_aggregate(
            self.agent_id,
            "ui_state",
            {"state": {"children": {self.app_key: {"defaultOpen": True}}}},
        )
        log.info(f"Pushed ui_state with {WIDGET_NAME} widget entry")