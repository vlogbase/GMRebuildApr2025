"""
Update CustomerReferral model to work with User model directly
"""
import os
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_customer_referral_model():
    """Update CustomerReferral model in models.py"""
    try:
        # Read the file
        with open('models.py', 'r') as f:
            content = f.read()
        
        # Backup the file
        backup_path = f"models.py.bak.{int(time.time())}"
        with open(backup_path, 'w') as f:
            f.write(content)
        logger.info(f"Created backup of models.py at {backup_path}")
        
        # Find the CustomerReferral class
        customer_referral_start = content.find("class CustomerReferral(db.Model):")
        if customer_referral_start == -1:
            logger.error("Could not find CustomerReferral class")
            return False
        
        # Find the end of the class
        class_end = content.find("\nclass ", customer_referral_start + 1)
        if class_end == -1:
            class_end = len(content)
        
        # Extract the CustomerReferral class
        customer_referral_class = content[customer_referral_start:class_end]
        
        # Update affiliate_id field to user_id
        old_affiliate_field = "affiliate_id = db.Column(db.Integer, db.ForeignKey('affiliate.id'))"
        new_user_field = "user_id = db.Column(db.Integer, db.ForeignKey('user.id'))"
        updated_class = customer_referral_class.replace(old_affiliate_field, new_user_field)
        
        # Update relationships
        old_relationship = "affiliate = db.relationship('Affiliate', foreign_keys=[affiliate_id])"
        new_relationship = "user = db.relationship('User', foreign_keys=[user_id])"
        updated_class = updated_class.replace(old_relationship, new_relationship)
        
        # Replace the class in the content
        updated_content = content.replace(customer_referral_class, updated_class)
        
        # Update tracking methods to use User instead of Affiliate
        track_method_start = updated_content.find("def track_referral(referral_code, user):")
        if track_method_start != -1:
            track_method_end = updated_content.find("\n    @classmethod", track_method_start)
            if track_method_end == -1:
                track_method_end = updated_content.find("\n\nclass ", track_method_start)
            
            old_track_method = updated_content[track_method_start:track_method_end]
            
            # Replace affiliate with user
            new_track_method = old_track_method.replace(
                "referring_affiliate = Affiliate.query.filter_by(referral_code=referred_by_code).first()",
                "referring_user = User.query.filter_by(referral_code=referred_by_code).first()"
            )
            
            new_track_method = new_track_method.replace(
                "if not referring_affiliate:",
                "if not referring_user:"
            )
            
            new_track_method = new_track_method.replace(
                "customer_referral = cls(\n                user_id=user.id,\n                affiliate_id=referring_affiliate.id,",
                "customer_referral = cls(\n                user_id=user.id,\n                referrer_id=referring_user.id,"
            )
            
            updated_content = updated_content.replace(old_track_method, new_track_method)
        
        # Write updated content
        with open('models.py', 'w') as f:
            f.write(updated_content)
        
        logger.info("Updated CustomerReferral model in models.py")
        return True
    except Exception as e:
        logger.error(f"Error updating CustomerReferral model: {e}")
        return False

def main():
    """Run all updates"""
    logger.info("Starting CustomerReferral model update")
    
    # Update CustomerReferral model
    if not update_customer_referral_model():
        logger.error("Failed to update CustomerReferral model")
        return False
    
    logger.info("Successfully updated CustomerReferral model")
    return True

if __name__ == "__main__":
    main()