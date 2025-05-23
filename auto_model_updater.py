"""
Automatic Model Updater
Runs in background to check for OpenRouter model changes and update all systems
"""

import threading
import time
import logging
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)

class AutoModelUpdater:
    def __init__(self, check_interval_minutes=5):
        self.check_interval = check_interval_minutes * 60  # Convert to seconds
        self.running = False
        self.thread = None
        self.last_update = None
        
    def start_monitoring(self):
        """Start the background monitoring thread"""
        if self.running:
            logger.info("Model monitoring already running")
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        logger.info(f"Started automatic model monitoring (checking every {self.check_interval/60} minutes)")
        
    def stop_monitoring(self):
        """Stop the background monitoring"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Stopped automatic model monitoring")
        
    def _monitor_loop(self):
        """Main monitoring loop that runs in background"""
        while self.running:
            try:
                self._check_and_update()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in model monitoring loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
                
    def _check_and_update(self):
        """Check for changes and update if needed"""
        try:
            from model_change_monitor import check_and_update_if_changed
            
            changed, message = check_and_update_if_changed()
            
            if changed:
                logger.info(f"🔄 Automatic model update triggered: {message}")
                self.last_update = datetime.utcnow()
                
                # Clear any cached data to ensure fresh data is served
                self._clear_caches()
                
                logger.info("✅ Automatic model update completed successfully")
            else:
                logger.debug(f"No model changes detected: {message}")
                
        except Exception as e:
            logger.error(f"Error during automatic model check: {e}")
            
    def _clear_caches(self):
        """Clear relevant caches after an update"""
        try:
            # Clear Redis caches if available
            try:
                from api_cache import clear_model_caches
                clear_model_caches()
                logger.info("Cleared model caches after update")
            except ImportError:
                logger.debug("Redis caching not available, skipping cache clear")
            except Exception as e:
                logger.warning(f"Error clearing caches: {e}")
                
        except Exception as e:
            logger.error(f"Error clearing caches: {e}")
            
    def force_update(self):
        """Force an immediate update check and refresh"""
        logger.info("🔄 Forcing immediate model update...")
        self._check_and_update()

# Global instance
auto_updater = AutoModelUpdater()

def init_auto_updater():
    """Initialize and start the automatic updater"""
    auto_updater.start_monitoring()
    
def stop_auto_updater():
    """Stop the automatic updater"""
    auto_updater.stop_monitoring()
    
def force_model_refresh():
    """Force an immediate model refresh"""
    auto_updater.force_update()