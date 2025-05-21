"""
Simple direct script to fix affiliate statuses in the database
"""
from app import app
from models import Affiliate
from database import db

def fix_all_affiliate_statuses():
    """Set all affiliate statuses to 'active' to prevent obsolete pages"""
    with app.app_context():
        # Count total affiliates
        total = Affiliate.query.count()
        print(f"Total affiliate records: {total}")
        
        # Find non-active affiliates
        non_active = Affiliate.query.filter(Affiliate.status != 'active').all()
        print(f"Found {len(non_active)} non-active affiliate records")
        
        # Update each one
        for aff in non_active:
            print(f"Updating affiliate ID {aff.id} from '{aff.status}' to 'active'")
            aff.status = 'active'
        
        # Commit changes
        db.session.commit()
        print(f"Successfully updated {len(non_active)} affiliate records to 'active'")

if __name__ == "__main__":
    fix_all_affiliate_statuses()