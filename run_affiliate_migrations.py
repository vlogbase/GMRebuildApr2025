"""
Run Affiliate System Migrations

This script sets up the necessary database tables for the affiliate system.
"""

import os
import sys
import logging
from app import app
from migrations_affiliate import run_migrations

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Run migrations for the affiliate system"""
    print("Running affiliate system migrations...")
    
    with app.app_context():
        result = run_migrations()
        
        if result:
            print("\n✅ Affiliate system migrations completed successfully")
            return 0
        else:
            print("\n❌ Affiliate system migrations failed")
            return 1

if __name__ == "__main__":
    sys.exit(main())