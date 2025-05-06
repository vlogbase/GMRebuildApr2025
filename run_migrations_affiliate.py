#!/usr/bin/env python3
"""
Run the affiliate system migrations.
This script sets up the database tables for the affiliate system.
"""

from app import app
from migrations_affiliate import run_migrations

def main():
    """Run the migrations with the Flask app context"""
    with app.app_context():
        success = run_migrations()
        if success:
            print("✅ Affiliate system migrations completed successfully!")
        else:
            print("❌ Affiliate system migrations failed! Check the logs for details.")

if __name__ == "__main__":
    main()