"""
Basic tests for an application.

This ensures all modules are importable and that the config is valid.
"""

def test_import_app():
    from processor.application import MaintenanceManagerApplication
    assert MaintenanceManagerApplication

    from dashboard.application import MaintenanceDashboardApp
    assert MaintenanceDashboardApp

def test_config():
    from dashboard.app_config import MaintenanceDashboardConfig

    config = MaintenanceDashboardConfig()
    assert isinstance(config.to_dict(), dict)

def test_ui():
    from processor.app_ui import MaintenanceManagerUI
    assert MaintenanceManagerUI
