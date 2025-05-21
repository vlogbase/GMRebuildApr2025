"""
Targeted fix for the PayPal email update feature in the affiliate blueprint
"""

def update_affiliate_file():
    """Update the PayPal email update function in the affiliate blueprint"""
    with open('affiliate_blueprint_improved.py', 'r') as f:
        content = f.read()
    
    # Fix the update_paypal_email function
    updated_content = content.replace(
        """@affiliate_bp.route('/update-paypal-email', methods=['POST'])
def update_paypal_email():
    """Update affiliate's PayPal email address"""
    # Import database models inside function to avoid circular imports
    from database import db
    from models import User, Affiliate""",
        """@affiliate_bp.route('/update-paypal-email', methods=['POST'])
def update_paypal_email():
    """Update affiliate's PayPal email address"""
    # Import database models inside function to avoid circular imports
    from database import db
    from models import User, Affiliate"""
    )
    
    with open('affiliate_blueprint_improved.py', 'w') as f:
        f.write(updated_content)
    
    print("Updated affiliate_blueprint_improved.py with fixed imports")

if __name__ == "__main__":
    update_affiliate_file()