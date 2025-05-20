"""
A simple script to link existing affiliates to users by email address.
This is a direct, lightweight implementation that avoids loading the full app.
"""

import os
import logging
from sqlalchemy import create_engine, text

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def link_affiliates_to_users():
    """Link existing affiliates to users based on email address."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        return False
        
    logger.info("Connecting to database...")
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as conn:
            # Start a transaction
            with conn.begin():
                # Find all unlinked affiliates
                result = conn.execute(text(
                    "SELECT id, email FROM affiliate WHERE user_id IS NULL"
                ))
                unlinked_affiliates = result.fetchall()
                
                if not unlinked_affiliates:
                    logger.info("No unlinked affiliates found")
                    return True
                    
                logger.info(f"Found {len(unlinked_affiliates)} unlinked affiliates")
                linked_count = 0
                
                # Link each affiliate to a user with the same email
                for affiliate_id, affiliate_email in unlinked_affiliates:
                    # Find user with matching email
                    result = conn.execute(text(
                        "SELECT id FROM \"user\" WHERE email = :email"
                    ), {"email": affiliate_email})
                    
                    user = result.fetchone()
                    
                    if user:
                        user_id = user[0]
                        logger.info(f"Linking affiliate {affiliate_id} to user {user_id}")
                        
                        # Update the affiliate record
                        conn.execute(text(
                            "UPDATE affiliate SET user_id = :user_id WHERE id = :affiliate_id"
                        ), {"user_id": user_id, "affiliate_id": affiliate_id})
                        
                        linked_count += 1
                    else:
                        logger.warning(f"No user found with email {affiliate_email} for affiliate {affiliate_id}")
                
                logger.info(f"Successfully linked {linked_count} affiliates to users")
                return True
                
    except Exception as e:
        logger.error(f"Error linking affiliates to users: {str(e)}")
        return False

if __name__ == "__main__":
    success = link_affiliates_to_users()
    if success:
        logger.info("✅ Affiliate linking completed successfully")
    else:
        logger.error("❌ Affiliate linking failed")