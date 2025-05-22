"""
Direct SQL migration script to move affiliate data to user table
"""
import os
import sys
import psycopg2
import logging
import uuid
import time
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def execute_sql(sql, params=None, fetch=False):
    """Execute SQL and optionally fetch results"""
    # Get database connection string from environment
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        return None
    
    conn = None
    try:
        # Connect to database
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # Execute SQL
        cursor.execute(sql, params or ())
        
        # Fetch results if requested
        result = None
        if fetch:
            result = cursor.fetchall()
        
        # Commit changes
        conn.commit()
        
        # Return result if any
        return result
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"SQL error: {e}")
        return None
    finally:
        if conn:
            conn.close()

def check_columns():
    """Check if columns already exist in user table"""
    columns = execute_sql(
        "SELECT column_name FROM information_schema.columns WHERE table_name = 'user'",
        fetch=True
    )
    
    if not columns:
        logger.error("Could not get column names for user table")
        return False
    
    column_names = [col[0] for col in columns]
    logger.info(f"Existing columns in user table: {column_names}")
    
    # Return if columns exist
    return {
        'paypal_email': 'paypal_email' in column_names,
        'referral_code': 'referral_code' in column_names,
        'referred_by_user_id': 'referred_by_user_id' in column_names
    }

def add_columns():
    """Add necessary columns to user table"""
    existing_columns = check_columns()
    
    if not existing_columns:
        logger.error("Could not check existing columns")
        return False
    
    try:
        # Add paypal_email column if it doesn't exist
        if not existing_columns['paypal_email']:
            execute_sql('ALTER TABLE "user" ADD COLUMN paypal_email VARCHAR(255)')
            logger.info("Added paypal_email column to user table")
        
        # Add referral_code column if it doesn't exist
        if not existing_columns['referral_code']:
            execute_sql('ALTER TABLE "user" ADD COLUMN referral_code VARCHAR(20) UNIQUE')
            logger.info("Added referral_code column to user table")
        
        # Add referred_by_user_id column if it doesn't exist
        if not existing_columns['referred_by_user_id']:
            execute_sql('ALTER TABLE "user" ADD COLUMN referred_by_user_id INTEGER REFERENCES "user" (id)')
            logger.info("Added referred_by_user_id column to user table")
        
        logger.info("Successfully added affiliate columns to user table")
        return True
    except Exception as e:
        logger.error(f"Error adding columns: {e}")
        return False

def generate_referral_codes():
    """Generate referral codes for all users who don't have one"""
    try:
        # First check how many users need referral codes
        result = execute_sql(
            'SELECT COUNT(*) FROM "user" WHERE referral_code IS NULL',
            fetch=True
        )
        
        if not result:
            logger.error("Could not count users without referral codes")
            return False
        
        count = result[0][0]
        if count == 0:
            logger.info("All users already have referral codes")
            return True
        
        logger.info(f"Generating referral codes for {count} users")
        
        # Get all users who need referral codes
        users = execute_sql(
            'SELECT id FROM "user" WHERE referral_code IS NULL',
            fetch=True
        )
        
        if not users:
            logger.warning("No users found that need referral codes")
            return False
        
        # Generate and update codes for each user
        for user in users:
            user_id = user[0]
            referral_code = str(uuid.uuid4())[:8]
            
            execute_sql(
                'UPDATE "user" SET referral_code = %s WHERE id = %s',
                (referral_code, user_id)
            )
            
            logger.info(f"Generated referral code {referral_code} for user {user_id}")
        
        logger.info("Successfully generated referral codes")
        return True
    except Exception as e:
        logger.error(f"Error generating referral codes: {e}")
        return False

def migrate_affiliate_data():
    """Migrate data from affiliate table to user table"""
    try:
        # First check if affiliate table exists
        tables = execute_sql(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'",
            fetch=True
        )
        
        if not tables:
            logger.error("Could not check tables")
            return False
        
        table_names = [table[0] for table in tables]
        if 'affiliate' not in table_names:
            logger.warning("Affiliate table does not exist, skipping migration")
            return True
        
        # Get all affiliate records
        affiliates = execute_sql(
            "SELECT id, name, email, paypal_email, referral_code, referred_by_affiliate_id FROM affiliate",
            fetch=True
        )
        
        if not affiliates:
            logger.warning("No affiliate records found to migrate")
            return True
        
        logger.info(f"Found {len(affiliates)} affiliate records to migrate")
        
        # Create a mapping of affiliate IDs to user IDs for the referred_by relationship
        affiliate_map = {}
        for affiliate in affiliates:
            affiliate_id = affiliate[0]
            email = affiliate[2]
            
            # Find the user ID for this affiliate
            user = execute_sql(
                'SELECT id FROM "user" WHERE email = %s',
                (email,),
                fetch=True
            )
            
            if user:
                user_id = user[0][0]
                affiliate_map[affiliate_id] = user_id
            else:
                logger.warning(f"Could not find user with email {email} for affiliate {affiliate_id}")
        
        # Update each user with their affiliate data
        updated_count = 0
        for affiliate in affiliates:
            affiliate_id = affiliate[0]
            email = affiliate[2]
            paypal_email = affiliate[3]
            referral_code = affiliate[4]
            referred_by_affiliate_id = affiliate[5]
            
            # Find the user for this affiliate
            user = execute_sql(
                'SELECT id FROM "user" WHERE email = %s',
                (email,),
                fetch=True
            )
            
            if not user:
                logger.warning(f"Could not find user with email {email} for affiliate {affiliate_id}")
                continue
            
            user_id = user[0][0]
            
            # Determine referred_by_user_id
            referred_by_user_id = None
            if referred_by_affiliate_id and referred_by_affiliate_id in affiliate_map:
                referred_by_user_id = affiliate_map[referred_by_affiliate_id]
            
            # Update user with affiliate data
            execute_sql(
                'UPDATE "user" SET paypal_email = %s, referral_code = %s, referred_by_user_id = %s WHERE id = %s',
                (paypal_email, referral_code, referred_by_user_id, user_id)
            )
            
            logger.info(f"Updated user {user_id} with affiliate data from affiliate {affiliate_id}")
            updated_count += 1
        
        logger.info(f"Successfully migrated {updated_count} affiliate records to user table")
        return True
    except Exception as e:
        logger.error(f"Error migrating affiliate data: {e}")
        return False

def create_update_paypal_route():
    """Create a simple PayPal email update route in app.py"""
    try:
        app_py_path = 'app.py'
        
        # Read the current app.py
        with open(app_py_path, 'r') as f:
            content = f.read()
        
        # Check if the route already exists
        if '@app.route("/update_paypal", methods=["POST"])' in content:
            logger.info("PayPal update route already exists")
            return True
        
        # Define the route to add
        route_code = """
# Simple route for updating PayPal email directly on the User model
@app.route("/update_paypal", methods=["POST"])
def update_paypal_email_direct():
    # Update PayPal email address for the current user
    if not current_user.is_authenticated:
        flash('Please login to update your PayPal email', 'warning')
        return redirect(url_for('login'))
    
    try:
        # Get the new email from form
        paypal_email = request.form.get('paypal_email', '').strip()
        
        if not paypal_email:
            flash('Please provide a PayPal email address', 'error')
            return redirect(url_for('billing.account_management', _anchor='tellFriend'))
        
        # Log the update
        old_email = current_user.paypal_email
        logger.info(f"Updating PayPal email for user {current_user.id} from '{old_email}' to '{paypal_email}'")
        
        # Update the user record
        current_user.paypal_email = paypal_email
        db.session.commit()
        
        # Show success message
        if old_email != paypal_email:
            flash(f'PayPal email updated successfully from {old_email or "not set"} to {paypal_email}!', 'success')
        else:
            flash('PayPal email unchanged', 'info')
        
    except Exception as e:
        logger.error(f"Error updating PayPal email: {e}", exc_info=True)
        db.session.rollback()
        flash('An error occurred. Please try again.', 'error')
    
    return redirect(url_for('billing.account_management', _anchor='tellFriend'))
"""
        
        # Add the route to app.py
        # Find a good insertion point - before the main route
        insertion_point = "@app.route('/')"
        if insertion_point in content:
            # Escape triple quotes in the route code for insertion
            escaped_route = route_code.replace('"""', '\\"\\"\\"')
            
            # Create a backup of app.py
            backup_path = f"{app_py_path}.bak.{int(time.time())}"
            with open(backup_path, 'w') as f:
                f.write(content)
            logger.info(f"Created backup of app.py at {backup_path}")
            
            # Insert the route and write the file
            new_content = content.replace(insertion_point, escaped_route + "\n\n" + insertion_point)
            with open(app_py_path, 'w') as f:
                f.write(new_content)
            
            logger.info("Added PayPal email update route to app.py")
            return True
        else:
            logger.warning("Could not find insertion point in app.py")
            return False
    except Exception as e:
        logger.error(f"Error updating app.py: {e}")
        return False

def main():
    """Run all migration steps"""
    logger.info("Starting direct affiliate migration")
    
    # Add columns to user table
    if not add_columns():
        logger.error("Failed to add columns to user table")
        return False
    
    # Generate referral codes for users who don't have one
    if not generate_referral_codes():
        logger.warning("Failed to generate referral codes, continuing anyway")
    
    # Migrate data from affiliate table to user table
    if not migrate_affiliate_data():
        logger.error("Failed to migrate affiliate data")
        return False
    
    # Create simple PayPal email update route
    if not create_update_paypal_route():
        logger.warning("Failed to create PayPal email update route, continuing anyway")
    
    logger.info("Migration completed successfully")
    return True

if __name__ == "__main__":
    main()