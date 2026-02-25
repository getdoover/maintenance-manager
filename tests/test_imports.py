"""
Basic tests for an application.

This ensures all modules are importable and that the config is valid.
"""

def test_import_app():
    from processor.application import MaintenanceManagerApplication
    assert MaintenanceManagerApplication

def test_config():
    from processor.app_config import MaintenanceManagerConfig

    config = MaintenanceManagerConfig()
    assert isinstance(config.to_dict(), dict)

def test_ui():
    from processor.app_ui import MaintenanceManagerUI
    assert MaintenanceManagerUI

def test_state():
    from processor.app_state import MaintenanceManagerState
    assert MaintenanceManagerState