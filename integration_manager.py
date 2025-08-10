from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from config.settings import settings

logger = logging.getLogger(__name__)


class IntegrationManager:
    """Central orchestration for all marketing technology integrations."""
    
    def __init__(self):
        self.active_integrations: Dict[str, Any] = {}
        self.sync_status: Dict[str, Dict] = {}
        
    def register_integration(self, name: str, connector: Any) -> bool:
        """Register a new integration connector."""
        try:
            self.active_integrations[name] = connector
            self.sync_status[name] = {
                "last_sync": None,
                "status": "inactive",
                "error_count": 0,
                "last_error": None
            }
            logger.info(f"Integration '{name}' registered successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to register integration '{name}': {e}")
            return False
    
    def start_integration(self, name: str) -> bool:
        """Start an integration and begin data synchronization."""
        if name not in self.active_integrations:
            logger.error(f"Integration '{name}' not found")
            return False
        
        try:
            connector = self.active_integrations[name]
            if hasattr(connector, 'connect'):
                connector.connect()
            
            self.sync_status[name]["status"] = "active"
            self.sync_status[name]["last_sync"] = datetime.now()
            logger.info(f"Integration '{name}' started successfully")
            return True
        except Exception as e:
            self.sync_status[name]["status"] = "error"
            self.sync_status[name]["last_error"] = str(e)
            self.sync_status[name]["error_count"] += 1
            logger.error(f"Failed to start integration '{name}': {e}")
            return False
    
    def stop_integration(self, name: str) -> bool:
        """Stop an integration and pause synchronization."""
        if name not in self.active_integrations:
            logger.error(f"Integration '{name}' not found")
            return False
        
        try:
            connector = self.active_integrations[name]
            if hasattr(connector, 'disconnect'):
                connector.disconnect()
            
            self.sync_status[name]["status"] = "inactive"
            logger.info(f"Integration '{name}' stopped successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to stop integration '{name}': {e}")
            return False
    
    def sync_all(self) -> Dict[str, bool]:
        """Perform synchronization across all active integrations."""
        results = {}
        for name, connector in self.active_integrations.items():
            if self.sync_status[name]["status"] == "active":
                results[name] = self._sync_integration(name, connector)
        return results
    
    def _sync_integration(self, name: str, connector: Any) -> bool:
        """Synchronize data for a specific integration."""
        try:
            if hasattr(connector, 'sync'):
                connector.sync()
            
            self.sync_status[name]["last_sync"] = datetime.now()
            self.sync_status[name]["last_error"] = None
            logger.info(f"Integration '{name}' synced successfully")
            return True
        except Exception as e:
            self.sync_status[name]["last_error"] = str(e)
            self.sync_status[name]["error_count"] += 1
            logger.error(f"Failed to sync integration '{name}': {e}")
            return False
    
    def get_integration_status(self, name: Optional[str] = None) -> Dict:
        """Get status information for integrations."""
        if name:
            return self.sync_status.get(name, {})
        return self.sync_status
    
    def get_active_integrations(self) -> List[str]:
        """Get list of currently active integrations."""
        return [
            name for name, status in self.sync_status.items()
            if status["status"] == "active"
        ]