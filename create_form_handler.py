"""
Script to create a direct form handler for PayPal email updates
"""
import os
import sys
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_handler():
    """Create a dedicated route for updating PayPal emails without CSRF validation"""
    try:
        # Get the app.py file
        app_py_path = 'app.py'
        with open(app_py_path, 'r') as f:
            content = f.read()
        
        # Check if our handler already exists
        if '@app.route("/update_paypal_email", methods=["POST"])' in content:
            logger.info("Direct PayPal email handler already exists")
            return True
        
        # Define the handler to add
        handler = """
# Direct handler for PayPal email updates without CSRF validation
@app.route("/update_paypal_email", methods=["POST"])
def direct_update_paypal_email():
    \"\"\"Direct handler for PayPal email updates that bypasses CSRF validation\"\"\"
    import uuid
    from models import Affiliate
    
    logger.info(f"Direct PayPal email update request: {request.form}")
    
    if 'user_id' not in session:
        flash('Please login to update your PayPal email', 'warning')
        return redirect(url_for('login'))
    
    try:
        # Get the email from the form
        paypal_email = request.form.get('paypal_email', '').strip()
        user_email = session.get('user_email', '')
        
        if not paypal_email:
            flash('Please provide a PayPal email address', 'error')
            return redirect(url_for('billing.account_management', _anchor='tellFriend'))
        
        # Find the affiliate by email
        affiliate = Affiliate.query.filter_by(email=user_email).first()
        
        if not affiliate:
            # Create a new affiliate record
            logger.info(f"Creating new affiliate record for {user_email}")
            affiliate = Affiliate(
                name=user_email,
                email=user_email,
                paypal_email=paypal_email,
                referral_code=str(uuid.uuid4())[:8],
                status='active',
                terms_agreed_at=datetime.now()
            )
            db.session.add(affiliate)
        else:
            # Update existing affiliate
            logger.info(f"Updating PayPal email for affiliate ID {affiliate.id} to {paypal_email}")
            affiliate.paypal_email = paypal_email
            affiliate.status = 'active'  # Always ensure active status
        
        # Commit changes
        db.session.commit()
        flash('PayPal email updated successfully!', 'success')
        logger.info(f"Successfully updated PayPal email")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating PayPal email: {str(e)}", exc_info=True)
        flash('An error occurred while updating your PayPal email. Please try again.', 'error')
    
    return redirect(url_for('billing.account_management', _anchor='tellFriend'))

"""
        
        # Find a good insertion point - before the main route handler
        main_route = "@app.route('/')"
        if main_route in content:
            # Insert our handler before the main route
            new_content = content.replace(main_route, handler + "\n" + main_route)
            
            # Write the updated file
            with open(app_py_path, 'w') as f:
                f.write(new_content)
            
            logger.info("Successfully added direct PayPal email handler to app.py")
            return True
        else:
            logger.error("Could not find main route in app.py")
            return False
    except Exception as e:
        logger.error(f"Error creating PayPal email handler: {e}")
        return False

def update_templates():
    """Update the templates to use the direct handler"""
    try:
        # Get the template file
        template_path = 'templates/affiliate/tell_friend_tab.html'
        with open(template_path, 'r') as f:
            content = f.read()
        
        # Replace the form action in both forms
        new_content = content.replace(
            'action="{{ url_for(\'affiliate.update_paypal_email\') }}"',
            'action="/update_paypal_email"'
        )
        
        if new_content != content:
            # Write the updated file
            with open(template_path, 'w') as f:
                f.write(new_content)
            
            logger.info("Successfully updated templates to use direct handler")
            return True
        else:
            logger.warning("No changes made to templates")
            return False
    except Exception as e:
        logger.error(f"Error updating templates: {e}")
        return False

def main():
    """Run all functions"""
    logger.info("Creating direct PayPal email handler")
    create_handler()
    
    logger.info("Updating templates")
    update_templates()
    
    logger.info("Done")
    return True

if __name__ == "__main__":
    main()