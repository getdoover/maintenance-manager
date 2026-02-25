from pydoover.docker import run_app

from .application import MaintenanceManagerApplication
from .app_config import MaintenanceManagerConfig

def main():
    """
    Run the application.
    """
    run_app(MaintenanceManagerApplication(config=MaintenanceManagerConfig()))
