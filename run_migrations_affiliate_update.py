#!/usr/bin/env python3
"""
Run the affiliate system update migrations.
This script updates the affiliate system tables.
"""

from app import app
from migrations_affiliate_update import run_migrations

def main():
    """Run the migrations with the Flask app context"""
    with app.app_context():
        success = run_migrations()
        if success:
            print("✅ Affiliate system update migrations completed successfully!")
        else:
            print("❌ Affiliate system update migrations failed! Check the logs for details.")

if __name__ == "__main__":
    main()