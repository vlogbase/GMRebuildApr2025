"""
Run the affiliate migration to link affiliates with users.
"""

import logging
from app import app, db
from migrations.affiliate_migration import run_migration

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    with app.app_context():
        logger.info("Starting affiliate migration...")
        success = run_migration(app, db)
        if success:
            logger.info("✅ Affiliate migration completed successfully")
        else:
            logger.error("❌ Affiliate migration failed")