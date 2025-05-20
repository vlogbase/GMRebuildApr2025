"""
Migration script to update usernames for Google-authenticated users.

This script updates existing users who authenticated with Google to use
their email addresses as usernames instead of their first names.
This prevents username conflicts with common names.
"""
import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError, IntegrityError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Update usernames for Google-authenticated users to use their email addresses."""
    logger.info("Starting Google username migration...")
    
    # Get database URL from environment variables
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL environment variable not set.")
        return False
    
    # Create database engine
    engine = create_engine(db_url)
    connection = engine.connect()
    
    try:
        # Start a transaction
        transaction = connection.begin()
        
        # First, get all users with Google IDs
        logger.info("Finding users authenticated with Google...")
        find_users_sql = text("""
            SELECT id, username, email, google_id 
            FROM "user" 
            WHERE google_id IS NOT NULL
        """)
        
        google_users = connection.execute(find_users_sql).fetchall()
        logger.info(f"Found {len(google_users)} Google-authenticated users.")
        
        if not google_users:
            logger.info("No Google users found to update. Migration completed.")
            transaction.commit()
            return True
        
        # Process each user
        updated_count = 0
        for user in google_users:
            user_id = user[0]
            current_username = user[1]
            email = user[2]
            
            # Convert email to a username by removing special characters
            # For simplicity, we'll use the part before @ as the base
            email_username = email.split('@')[0]
            
            # Skip if the username is already the email username
            if current_username == email:
                logger.info(f"User {user_id} already has email as username. Skipping.")
                continue
                
            try:
                # Try to update the username to the email
                update_sql = text("""
                    UPDATE "user" 
                    SET username = :new_username 
                    WHERE id = :user_id
                """)
                
                connection.execute(update_sql, {"new_username": email, "user_id": user_id})
                updated_count += 1
                logger.info(f"Updated user {user_id}: changed username from '{current_username}' to '{email}'")
                
            except IntegrityError:
                # Handle the case where the email is already used as username
                logger.info(f"Email {email} already in use as username for another user")
                
                # We need to create a new transaction after rollback
                if 'transaction' in locals():
                    transaction.rollback()
                
                # Start a new transaction
                transaction = connection.begin()
                
                # Create a unique username by adding a suffix
                suffix = 1
                success = False
                
                while not success and suffix < 1000:  # Safety limit
                    try:
                        unique_username = f"{email}_{suffix}"
                        update_sql = text("""
                            UPDATE "user" 
                            SET username = :new_username 
                            WHERE id = :user_id
                        """)
                        
                        connection.execute(update_sql, {"new_username": unique_username, "user_id": user_id})
                        updated_count += 1
                        logger.info(f"Updated user {user_id} with unique username: '{unique_username}'")
                        success = True
                    except IntegrityError:
                        # If still a conflict, increment the suffix and try again
                        logger.info(f"Username {unique_username} already in use, trying next suffix")
                        suffix += 1
                        
                        # Rollback and start a new transaction
                        transaction.rollback()
                        transaction = connection.begin()
        
        # Commit all changes
        transaction.commit()
        logger.info(f"Google username migration completed successfully. Updated {updated_count} users.")
        return True
        
    except (OperationalError, ProgrammingError) as e:
        logger.error(f"Error during migration: {e}")
        transaction.rollback()
        return False
    finally:
        connection.close()

if __name__ == "__main__":
    run_migration()