"""
Script to update the Tell a Friend tab template to use User model fields instead of Affiliate
"""
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_template():
    """Update the Tell a Friend tab template to use User model fields"""
    try:
        # Read the current template
        template_path = 'templates/affiliate/tell_friend_tab.html'
        with open(template_path, 'r') as f:
            content = f.read()
        
        # Replace references to affiliate with current_user
        updated_content = content
        
        # Replace affiliate.paypal_email with current_user.paypal_email
        updated_content = updated_content.replace('affiliate.paypal_email', 'current_user.paypal_email')
        
        # Replace affiliate.referral_code with current_user.referral_code
        updated_content = updated_content.replace('affiliate.referral_code', 'current_user.referral_code')
        
        # Replace affiliate status checks with simple logged-in checks
        updated_content = updated_content.replace(
            '{% if affiliate and affiliate.status == \'active\' %}',
            '{% if current_user.is_authenticated %}'
        )
        
        # Create a backup of the original file
        backup_path = f"{template_path}.bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        with open(backup_path, 'w') as f:
            f.write(content)
        logger.info(f"Created backup at {backup_path}")
        
        # Write the updated content
        with open(template_path, 'w') as f:
            f.write(updated_content)
        
        logger.info("Successfully updated Tell a Friend template")
        return True
    except Exception as e:
        logger.error(f"Error updating template: {e}")
        return False

def create_paypal_email_update_route():
    """Create a simple route for updating PayPal email in app.py"""
    try:
        app_py_path = 'app.py'
        with open(app_py_path, 'r') as f:
            content = f.read()
        
        # Check if our route already exists
        if '@app.route("/update_paypal_email_simple", methods=["POST"])' in content:
            logger.info("PayPal email update route already exists")
            return True
        
        # Define the new route
        new_route = """
# Simple route for updating PayPal email directly on the User model
@app.route("/update_paypal_email_simple", methods=["POST"])
def update_paypal_email_simple():
    \"\"\"Update the user's PayPal email address\"\"\"
    if not current_user.is_authenticated:
        flash('Please login to update your PayPal email', 'warning')
        return redirect(url_for('login'))
    
    try:
        # Get the new email
        paypal_email = request.form.get('paypal_email', '').strip()
        
        if not paypal_email:
            flash('Please provide a PayPal email address', 'error')
            return redirect(url_for('billing.account_management', _anchor='tellFriend'))
        
        # Log the current value
        old_email = current_user.paypal_email
        logger.info(f"Updating PayPal email for user {current_user.id} from '{old_email}' to '{paypal_email}'")
        
        # Update the user's PayPal email
        current_user.paypal_email = paypal_email
        db.session.commit()
        
        # Show a success message
        if old_email != paypal_email:
            flash(f'PayPal email updated successfully from {old_email or "not set"} to {paypal_email}!', 'success')
        else:
            flash('PayPal email unchanged', 'info')
        
    except Exception as e:
        logger.error(f"Error updating PayPal email: {e}", exc_info=True)
        db.session.rollback()
        flash('An error occurred while updating your PayPal email. Please try again.', 'error')
    
    return redirect(url_for('billing.account_management', _anchor='tellFriend'))
"""
        
        # Find a good insertion point - before the main route
        main_route = "@app.route('/')"
        if main_route in content:
            # Insert our route before the main route
            new_content = content.replace(main_route, new_route + "\n\n" + main_route)
            
            # Create a backup
            backup_path = f"{app_py_path}.bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            with open(backup_path, 'w') as f:
                f.write(content)
            logger.info(f"Created backup at {backup_path}")
            
            # Write the updated content
            with open(app_py_path, 'w') as f:
                f.write(new_content)
            
            logger.info("Successfully added PayPal email update route to app.py")
            return True
        else:
            logger.error("Could not find main route in app.py")
            return False
    except Exception as e:
        logger.error(f"Error creating PayPal email update route: {e}")
        return False

def update_form_action():
    """Update the form action in the template"""
    try:
        template_path = 'templates/affiliate/tell_friend_tab.html'
        with open(template_path, 'r') as f:
            content = f.read()
        
        # Replace the form action
        updated_content = content.replace(
            'action="/update_paypal_email"',
            'action="/update_paypal_email_simple"'
        )
        
        # Write the updated content
        with open(template_path, 'w') as f:
            f.write(updated_content)
        
        logger.info("Successfully updated form action in template")
        return True
    except Exception as e:
        logger.error(f"Error updating form action: {e}")
        return False

def main():
    """Run all update steps"""
    logger.info("Starting template updates")
    
    # Update the template
    update_template()
    
    # Create the PayPal email update route
    create_paypal_email_update_route()
    
    # Update the form action
    update_form_action()
    
    logger.info("Updates completed")
    return True

if __name__ == "__main__":
    main()