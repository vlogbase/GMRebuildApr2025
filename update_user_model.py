"""
Update User model to include affiliate functionality
"""
import os
import logging
import time
import random
import string
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def read_models_file():
    """Read the models.py file"""
    try:
        with open('models.py', 'r') as f:
            content = f.read()
        return content
    except Exception as e:
        logger.error(f"Error reading models.py: {e}")
        return None

def backup_models_file(content):
    """Create a backup of models.py"""
    try:
        backup_path = f"models.py.bak.{int(time.time())}"
        with open(backup_path, 'w') as f:
            f.write(content)
        logger.info(f"Created backup of models.py at {backup_path}")
        return True
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        return False

def update_user_model(content):
    """Update the User model with affiliate fields and methods"""
    try:
        # Check if the model already has the necessary fields
        if "paypal_email" in content and "referral_code" in content and "referred_by_user_id" in content:
            logger.info("User model already has affiliate fields")
            return content
        
        # Find the User model class
        user_class_start = content.find("class User(")
        if user_class_start == -1:
            logger.error("Could not find User class in models.py")
            return content
        
        # Find the end of the class definition (next class or end of file)
        next_class = content.find("class ", user_class_start + 10)
        if next_class == -1:
            user_class_end = len(content)
        else:
            user_class_end = next_class
        
        # Extract the User class
        user_class = content[user_class_start:user_class_end]
        
        # Check if the fields already exist (partial matching)
        if "paypal_email" in user_class and "referral_code" in user_class and "referred_by_user_id" in user_class:
            logger.info("User model already has affiliate fields")
            return content
        
        # Find the last field in the User class
        last_field_end = user_class.rfind(")")
        field_insert_pos = user_class.rfind("\n", 0, last_field_end)
        
        # Prepare the new fields
        new_fields = """
    # Affiliate fields
    paypal_email = db.Column(db.String(255), nullable=True)
    referral_code = db.Column(db.String(16), unique=True, nullable=True, index=True)
    referred_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    referred_users = db.relationship('User', backref=db.backref('referred_by', remote_side='User.id'), lazy='dynamic')
"""
        
        # Insert the new fields
        updated_user_class = user_class[:field_insert_pos] + new_fields + user_class[field_insert_pos:]
        
        # Prepare the new methods
        methods = """
    def generate_referral_code(self):
        \"\"\"Generate a unique referral code for this user\"\"\"
        if self.referral_code:
            return self.referral_code
            
        # Generate a random code
        while True:
            # Generate a random string of 8 characters
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            
            # Check if the code is already in use
            existing = User.query.filter_by(referral_code=code).first()
            if not existing:
                self.referral_code = code
                return code
                
    def update_paypal_email(self, email):
        \"\"\"Update the PayPal email for this user\"\"\"
        self.paypal_email = email
        return True
        
    def get_referrals(self):
        \"\"\"Get all users referred by this user\"\"\"
        return User.query.filter_by(referred_by_user_id=self.id).all()
        
    def get_commissions(self):
        \"\"\"Get all commissions earned by this user\"\"\"
        from models import Commission
        return Commission.query.filter_by(user_id=self.id).all()
"""
        
        # Add the methods if they don't already exist
        if "def generate_referral_code" not in updated_user_class:
            method_insert_pos = updated_user_class.rfind("\n")
            updated_user_class = updated_user_class[:method_insert_pos] + methods + updated_user_class[method_insert_pos:]
        
        # Replace the old User class with the updated one
        updated_content = content[:user_class_start] + updated_user_class + content[user_class_end:]
        
        return updated_content
    except Exception as e:
        logger.error(f"Error updating User model: {e}")
        return content

def update_customer_referral_model(content):
    """Update the CustomerReferral model to use User instead of Affiliate"""
    try:
        # Find the CustomerReferral model class
        model_start = content.find("class CustomerReferral(")
        if model_start == -1:
            logger.error("Could not find CustomerReferral class in models.py")
            return content
        
        # Find the end of the class definition (next class or end of file)
        next_class = content.find("class ", model_start + 10)
        if next_class == -1:
            model_end = len(content)
        else:
            model_end = next_class
        
        # Extract the CustomerReferral class
        model_class = content[model_start:model_end]
        
        # Check if the model already uses user_id instead of affiliate_id
        if "user_id = db.Column" in model_class and "affiliate_id" not in model_class:
            logger.info("CustomerReferral model already updated")
            return content
        
        # Replace affiliate_id with user_id and add track_referral method
        updated_model_class = model_class.replace("affiliate_id", "user_id").replace("Affiliate", "User")
        
        # Add track_referral method if it doesn't exist
        if "def track_referral" not in updated_model_class:
            track_method = """
    @classmethod
    def track_referral(cls, referral_code, user):
        \"\"\"
        Track a referral from a referral code
        
        Args:
            referral_code (str): The referral code
            user (User): The user being referred
            
        Returns:
            CustomerReferral: The created customer referral record
        \"\"\"
        from models import User
        
        # Find the referring user
        referring_user = User.query.filter_by(referral_code=referral_code).first()
        if not referring_user:
            return None
            
        # Create the customer referral
        referral = cls(
            user_id=user.id,
            referrer_id=referring_user.id,
            referral_level=1
        )
        
        # Add and commit
        from app import db
        db.session.add(referral)
        db.session.commit()
        
        return referral
"""
            method_insert_pos = updated_model_class.rfind("\n")
            updated_model_class = updated_model_class[:method_insert_pos] + track_method + updated_model_class[method_insert_pos:]
        
        # Replace the old CustomerReferral class with the updated one
        updated_content = content[:model_start] + updated_model_class + content[model_end:]
        
        return updated_content
    except Exception as e:
        logger.error(f"Error updating CustomerReferral model: {e}")
        return content

def update_commission_model(content):
    """Update the Commission model to use user_id instead of affiliate_id"""
    try:
        # Find the Commission model class
        model_start = content.find("class Commission(")
        if model_start == -1:
            logger.error("Could not find Commission class in models.py")
            return content
        
        # Find the end of the class definition (next class or end of file)
        next_class = content.find("class ", model_start + 10)
        if next_class == -1:
            model_end = len(content)
        else:
            model_end = next_class
        
        # Extract the Commission class
        model_class = content[model_start:model_end]
        
        # Check if the model already uses user_id instead of affiliate_id
        if "user_id = db.Column" in model_class and "affiliate_id" not in model_class:
            logger.info("Commission model already updated")
            return content
        
        # Replace affiliate_id with user_id and update __repr__ method
        updated_model_class = model_class.replace("affiliate_id", "user_id").replace("Affiliate", "User")
        
        # Update the __repr__ method if it exists
        if "def __repr__" in updated_model_class:
            # Find the __repr__ method
            repr_start = updated_model_class.find("def __repr__")
            repr_end = updated_model_class.find(")", repr_start)
            
            # Replace affiliate_id with user_id in the __repr__ method
            old_repr = updated_model_class[repr_start:repr_end+1]
            new_repr = old_repr.replace("affiliate_id", "user_id")
            
            updated_model_class = updated_model_class.replace(old_repr, new_repr)
        
        # Replace the old Commission class with the updated one
        updated_content = content[:model_start] + updated_model_class + content[model_end:]
        
        return updated_content
    except Exception as e:
        logger.error(f"Error updating Commission model: {e}")
        return content

def main():
    """Update models.py with all changes"""
    logger.info("Starting models.py update")
    
    # Read the models file
    content = read_models_file()
    if not content:
        return False
    
    # Create backup
    if not backup_models_file(content):
        return False
    
    # Update User model
    updated_content = update_user_model(content)
    
    # Update CustomerReferral model
    updated_content = update_customer_referral_model(updated_content)
    
    # Update Commission model
    updated_content = update_commission_model(updated_content)
    
    # Write updated content
    try:
        with open('models.py', 'w') as f:
            f.write(updated_content)
        logger.info("Successfully updated models.py")
        return True
    except Exception as e:
        logger.error(f"Error writing models.py: {e}")
        return False

if __name__ == "__main__":
    main()