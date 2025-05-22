"""
Update affiliate system to use User model directly instead of separate Affiliate table
"""
import os
import sys
import psycopg2
import logging
from datetime import datetime
import uuid
import time

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_database():
    """Check database connection and status"""
    # Get database connection string from environment
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        return False
    
    try:
        # Connect to database
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # Check if database connection works
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        logger.info(f"Connected to PostgreSQL: {version[0]}")
        
        # Check if user table exists
        cursor.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'user')")
        user_table_exists = cursor.fetchone()[0]
        
        if not user_table_exists:
            logger.error("User table does not exist")
            return False
            
        logger.info("User table exists")
        
        # Check if affiliate fields exist in user table
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'user'")
        columns = [col[0] for col in cursor.fetchall()]
        
        # Log existing columns
        logger.info(f"Existing columns in user table: {columns}")
        
        # Check for required affiliate fields
        has_paypal_email = 'paypal_email' in columns
        has_referral_code = 'referral_code' in columns
        has_referred_by = 'referred_by_user_id' in columns
        
        logger.info(f"Affiliate fields in user table: paypal_email={has_paypal_email}, referral_code={has_referral_code}, referred_by_user_id={has_referred_by}")
        
        # Check if affiliate table exists
        cursor.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'affiliate')")
        affiliate_table_exists = cursor.fetchone()[0]
        
        logger.info(f"Affiliate table exists: {affiliate_table_exists}")
        
        # Close connections
        cursor.close()
        conn.close()
        
        return True
    except Exception as e:
        logger.error(f"Error checking database: {e}")
        return False

def create_fields():
    """Create affiliate fields in user table if they don't exist"""
    # Get database connection string from environment
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        return False
    
    try:
        # Connect to database
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # Check if fields exist
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'user'")
        columns = [col[0] for col in cursor.fetchall()]
        
        # Add paypal_email if it doesn't exist
        if 'paypal_email' not in columns:
            logger.info("Adding paypal_email column to user table")
            cursor.execute('ALTER TABLE "user" ADD COLUMN paypal_email VARCHAR(255)')
        
        # Add referral_code if it doesn't exist
        if 'referral_code' not in columns:
            logger.info("Adding referral_code column to user table")
            cursor.execute('ALTER TABLE "user" ADD COLUMN referral_code VARCHAR(20) UNIQUE')
        
        # Add referred_by_user_id if it doesn't exist
        if 'referred_by_user_id' not in columns:
            logger.info("Adding referred_by_user_id column to user table")
            cursor.execute('ALTER TABLE "user" ADD COLUMN referred_by_user_id INTEGER REFERENCES "user" (id)')
        
        # Commit changes
        conn.commit()
        
        # Generate referral codes for users without them
        cursor.execute('SELECT COUNT(*) FROM "user" WHERE referral_code IS NULL')
        null_count = cursor.fetchone()[0]
        
        if null_count > 0:
            logger.info(f"Generating referral codes for {null_count} users")
            cursor.execute('SELECT id FROM "user" WHERE referral_code IS NULL')
            users = cursor.fetchall()
            
            for user in users:
                user_id = user[0]
                referral_code = str(uuid.uuid4())[:8].upper()
                cursor.execute('UPDATE "user" SET referral_code = %s WHERE id = %s', (referral_code, user_id))
                logger.info(f"Generated referral code {referral_code} for user {user_id}")
            
            conn.commit()
        
        # Close connections
        cursor.close()
        conn.close()
        
        return True
    except Exception as e:
        logger.error(f"Error creating fields: {e}")
        if 'conn' in locals() and conn:
            conn.rollback()
        return False

def migrate_data():
    """Migrate data from affiliate table to user table"""
    # Get database connection string from environment
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        return False
    
    try:
        # Connect to database
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # Check if affiliate table exists
        cursor.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'affiliate')")
        affiliate_table_exists = cursor.fetchone()[0]
        
        if not affiliate_table_exists:
            logger.info("Affiliate table does not exist, no migration needed")
            return True
        
        # Count affiliates
        cursor.execute("SELECT COUNT(*) FROM affiliate")
        affiliate_count = cursor.fetchone()[0]
        logger.info(f"Found {affiliate_count} affiliates to migrate")
        
        # If no affiliates, no migration needed
        if affiliate_count == 0:
            return True
        
        # Migrate affiliate data to user table
        cursor.execute("""
            SELECT a.id, a.email, a.paypal_email, a.referral_code, a.referred_by_affiliate_id 
            FROM affiliate a 
            WHERE a.status = 'active'
        """)
        affiliates = cursor.fetchall()
        
        # Create mapping from affiliate ID to user ID
        affiliate_to_user = {}
        for affiliate in affiliates:
            affiliate_id = affiliate[0]
            email = affiliate[1]
            
            cursor.execute('SELECT id FROM "user" WHERE email = %s', (email,))
            user = cursor.fetchone()
            
            if user:
                affiliate_to_user[affiliate_id] = user[0]
        
        # Update user records with affiliate data
        updated_count = 0
        for affiliate in affiliates:
            affiliate_id = affiliate[0]
            email = affiliate[1]
            paypal_email = affiliate[2]
            referral_code = affiliate[3]
            referred_by_affiliate_id = affiliate[4]
            
            # Find corresponding user
            cursor.execute('SELECT id FROM "user" WHERE email = %s', (email,))
            user = cursor.fetchone()
            
            if not user:
                logger.warning(f"No user found for affiliate email {email}")
                continue
            
            user_id = user[0]
            
            # Find referred_by_user_id
            referred_by_user_id = None
            if referred_by_affiliate_id and referred_by_affiliate_id in affiliate_to_user:
                referred_by_user_id = affiliate_to_user[referred_by_affiliate_id]
            
            # Update user
            cursor.execute("""
                UPDATE "user" 
                SET paypal_email = %s, 
                    referral_code = %s, 
                    referred_by_user_id = %s
                WHERE id = %s
            """, (paypal_email, referral_code, referred_by_user_id, user_id))
            
            updated_count += 1
        
        logger.info(f"Updated {updated_count} users with affiliate data")
        
        # Commit changes
        conn.commit()
        
        # Close connections
        cursor.close()
        conn.close()
        
        return True
    except Exception as e:
        logger.error(f"Error migrating data: {e}")
        if 'conn' in locals() and conn:
            conn.rollback()
        return False

def create_paypal_update_route():
    """Create direct PayPal update route in app.py"""
    try:
        # Check if app.py exists
        if not os.path.exists('app.py'):
            logger.error("app.py does not exist")
            return False
        
        # Read app.py
        with open('app.py', 'r') as f:
            app_content = f.read()
        
        # Check if route already exists
        if '@app.route("/update_paypal", methods=["POST"])' in app_content:
            logger.info("PayPal update route already exists")
            return True
        
        # Create backup of app.py
        backup_file = f"app.py.bak.{int(time.time())}"
        with open(backup_file, 'w') as f:
            f.write(app_content)
        logger.info(f"Created backup of app.py at {backup_file}")
        
        # Find insertion point
        insertion_point = "@app.route('/')"
        
        if insertion_point not in app_content:
            logger.error("Could not find insertion point in app.py")
            return False
        
        # PayPal update route
        paypal_route = """
# Direct PayPal email update route
@app.route("/update_paypal", methods=["POST"])
def update_paypal_email_direct():
    # Update PayPal email address for the current user
    if not current_user.is_authenticated:
        flash('Please login to update your PayPal email', 'warning')
        return redirect(url_for('login'))
    
    try:
        # Get form data
        paypal_email = request.form.get('paypal_email', '').strip()
        
        if not paypal_email:
            flash('Please provide a PayPal email address', 'error')
            return redirect(url_for('billing.account_management', _anchor='tellFriend'))
        
        # Log the update attempt
        logger.info(f"Updating PayPal email for user {current_user.id} from '{current_user.paypal_email or 'None'}' to '{paypal_email}'")
        
        # Update user record
        current_user.paypal_email = paypal_email
        db.session.commit()
        
        flash('PayPal email updated successfully!', 'success')
        
    except Exception as e:
        logger.error(f"Error updating PayPal email: {e}", exc_info=True)
        db.session.rollback()
        flash('An error occurred updating your PayPal email. Please try again.', 'error')
    
    return redirect(url_for('billing.account_management', _anchor='tellFriend'))

"""
        
        # Insert route
        new_content = app_content.replace(insertion_point, paypal_route + "\n" + insertion_point)
        
        # Write updated app.py
        with open('app.py', 'w') as f:
            f.write(new_content)
        
        logger.info("Added PayPal update route to app.py")
        return True
    except Exception as e:
        logger.error(f"Error creating PayPal update route: {e}")
        return False

def update_tell_friend_template():
    """Update Tell-a-Friend template to use new fields and form action"""
    try:
        template_path = "templates/affiliate/tell_friend_tab.html"
        
        # Check if template exists
        if not os.path.exists(template_path):
            logger.error(f"Template {template_path} does not exist")
            return False
        
        # Read template
        with open(template_path, 'r') as f:
            template_content = f.read()
        
        # Create backup
        backup_file = f"{template_path}.bak.{int(time.time())}"
        with open(backup_file, 'w') as f:
            f.write(template_content)
        logger.info(f"Created backup of template at {backup_file}")
        
        # Update form action to use direct route
        updated_content = template_content.replace(
            'action="{{ url_for(\'affiliate.update_paypal_email\') }}"', 
            'action="/update_paypal"'
        )
        
        # Update display of PayPal email to use current_user.paypal_email
        updated_content = updated_content.replace(
            '{% if affiliate.paypal_email %}{{ affiliate.paypal_email }}{% else %}Not set{% endif %}',
            '{% if current_user.paypal_email %}{{ current_user.paypal_email }}{% else %}Not set{% endif %}'
        )
        
        # Update input value to use current_user.paypal_email
        updated_content = updated_content.replace(
            'value="{% if affiliate.paypal_email %}{{ affiliate.paypal_email }}{% endif %}"',
            'value="{% if current_user.paypal_email %}{{ current_user.paypal_email }}{% endif %}"'
        )
        
        # Update referral code display to use current_user.referral_code
        updated_content = updated_content.replace(
            '{{ affiliate.referral_code }}',
            '{{ current_user.referral_code }}'
        )
        
        # Write updated template
        with open(template_path, 'w') as f:
            f.write(updated_content)
        
        logger.info(f"Updated template {template_path}")
        return True
    except Exception as e:
        logger.error(f"Error updating template: {e}")
        return False

def main():
    """Run all steps to update affiliate system"""
    logger.info("Starting affiliate system update")
    
    # Check database
    if not check_database():
        logger.error("Database check failed")
        return False
    
    # Create fields in user table
    if not create_fields():
        logger.error("Failed to create fields in user table")
        return False
    
    # Migrate data from affiliate table
    if not migrate_data():
        logger.error("Failed to migrate data from affiliate table")
        return False
    
    # Create direct PayPal update route
    if not create_paypal_update_route():
        logger.error("Failed to create PayPal update route")
        return False
    
    # Update Tell-a-Friend template
    if not update_tell_friend_template():
        logger.error("Failed to update Tell-a-Friend template")
        return False
    
    logger.info("Affiliate system update completed successfully")
    return True

if __name__ == "__main__":
    main()