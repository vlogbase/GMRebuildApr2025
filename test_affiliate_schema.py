#!/usr/bin/env python3
"""
Test script to verify the affiliate table schema has been updated correctly.
"""

from app import app, db
from models import Affiliate
import sqlalchemy

def test_schema():
    """Test the affiliate table schema"""
    with app.app_context():
        try:
            # Get the first affiliate record
            affiliate = Affiliate.query.first()
            
            print(f"Affiliate found: {affiliate is not None}")
            
            if affiliate:
                print(f"Has terms_agreed_at attribute: {hasattr(affiliate, 'terms_agreed_at')}")
                print(f"Paypal email is nullable: {Affiliate.__table__.columns['paypal_email'].nullable}")
            
            # Check table info directly from SQLAlchemy
            inspector = db.inspect(db.engine)
            columns = {c['name']: c for c in inspector.get_columns('affiliate')}
            
            print(f"\nAffiliate table columns: {list(columns.keys())}")
            
            if 'terms_agreed_at' in columns:
                print(f"terms_agreed_at column exists in database schema")
                print(f"terms_agreed_at is nullable: {columns['terms_agreed_at']['nullable']}")
            else:
                print(f"terms_agreed_at column is MISSING from database schema")
                
            if 'paypal_email' in columns:
                print(f"paypal_email is nullable: {columns['paypal_email']['nullable']}")
            
            # Test querying the column explicitly
            print("\nTesting database query with terms_agreed_at...")
            test_query = db.session.query(Affiliate.id, Affiliate.terms_agreed_at).first()
            print(f"Query successful: {test_query is not None}")
            
            return True
            
        except sqlalchemy.exc.ProgrammingError as e:
            print(f"ERROR - SQL Error: {e}")
            return False
        except Exception as e:
            print(f"ERROR - General Error: {e}")
            return False

if __name__ == "__main__":
    success = test_schema()
    if success:
        print("\n✅ Affiliate schema test completed successfully!")
    else:
        print("\n❌ Affiliate schema test failed!")