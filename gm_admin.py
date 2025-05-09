"""
Admin Module for GloriaMundo Chatbot

This module handles admin routes and views using Flask-Admin.
It provides a secure admin interface for managing the affiliate system.
"""

import os
import logging
from datetime import datetime
from flask import redirect, url_for, request, abort, flash
from flask_admin import Admin, AdminIndexView, expose, BaseView
from flask_admin.contrib.sqla import ModelView
from flask_admin.actions import action
from flask_login import current_user
from sqlalchemy import func, desc

logger = logging.getLogger(__name__)

# Fallback function if PayPal module not available
def process_paypal_payouts(affiliate_commissions):
    """Dummy function if paypal_payouts module isn't available"""
    logger.warning("PayPal payouts module not imported, using fallback")
    # In a real implementation, this would call the actual PayPal API
    return {"batch_id": f"FALLBACK_{datetime.now().strftime('%Y%m%d%H%M%S')}", "status": "PENDING"}

# Try to import the real PayPal payout function
try:
    from affiliate import process_paypal_payouts as actual_process_paypal_payouts
    process_paypal_payouts = actual_process_paypal_payouts
    logger.info("Successfully imported PayPal payouts module")
except ImportError:
    logger.warning("Could not import PayPal payouts module, using fallback")

class SecureBaseView:
    """Base view with security features for all admin views"""
    def is_accessible(self):
        """Only allow access to admin users (email: andy@sentigral.com)"""
        if not current_user.is_authenticated:
            return False
        
        admin_emails = os.environ.get('ADMIN_EMAILS', 'andy@sentigral.com').split(',')
        admin_emails = [email.strip() for email in admin_emails if email.strip()]
        
        return current_user.email in admin_emails
    
    def inaccessible_callback(self, name, **kwargs):
        """Redirect to login page if user doesn't have access"""
        if not current_user.is_authenticated:
            return redirect(url_for('login', next=request.url))
        return abort(403)  # Forbidden

class SecureAdminIndexView(AdminIndexView, SecureBaseView):
    """Secure index view for admin panel"""
    @expose('/')
    def index(self):
        """Admin dashboard home page with overview statistics"""
        logger.info("Rendering admin dashboard")
        
        # Access to models only after app context is available
        from models import User, Affiliate, Commission, Usage
        
        # Basic stats
        user_count = User.query.count()
        affiliate_count = Affiliate.query.count()
        commission_count = Commission.query.count()
        pending_commissions = Commission.query.filter_by(status='pending').count()
        approved_commissions = Commission.query.filter_by(status='approved').count()
        paid_commissions = Commission.query.filter_by(status='paid').count()
        rejected_commissions = Commission.query.filter_by(status='rejected').count()
        
        # Total commission amounts
        total_pending = Commission.query.filter_by(status='pending').with_entities(
            func.sum(Commission.commission_amount)).scalar() or 0
        total_approved = Commission.query.filter_by(status='approved').with_entities(
            func.sum(Commission.commission_amount)).scalar() or 0
        total_paid = Commission.query.filter_by(status='paid').with_entities(
            func.sum(Commission.commission_amount)).scalar() or 0
        
        return self.render('admin/index.html',
                          user_count=user_count,
                          affiliate_count=affiliate_count,
                          commission_count=commission_count,
                          pending_commissions=pending_commissions,
                          approved_commissions=approved_commissions,
                          paid_commissions=paid_commissions,
                          rejected_commissions=rejected_commissions,
                          total_pending=total_pending,
                          total_approved=total_approved,
                          total_paid=total_paid)

class CommissionModelView(ModelView, SecureBaseView):
    """Commission management view"""
    column_list = [
        'id', 'affiliate.email', 'commission_level', 'purchase_amount_base', 
        'commission_amount', 'status', 'commission_earned_date', 
        'commission_available_date', 'payout_batch_id'
    ]
    
    def _get_affiliate_email(view, context, model, name):
        """Get the affiliate email for display"""
        if model.affiliate:
            return model.affiliate.email
        return "N/A"
    
    column_formatters = {
        'affiliate.email': _get_affiliate_email,
        'purchase_amount_base': lambda v, c, m, p: f'£{m.purchase_amount_base:.2f}',
        'commission_amount': lambda v, c, m, p: f'£{m.commission_amount:.2f}'
    }
    
    column_default_sort = ('commission_available_date', True)
    column_filters = ['status', 'commission_available_date', 'commission_level']
    
    # Allow for editing status but not creating commissions manually
    can_create = False  # Commissions are created automatically through the affiliate system
    can_edit = True     # Allow editing of status and other fields
    
    @action('approve', 'Approve', 'Are you sure you want to approve the selected commissions?')
    def approve_commission(self, ids):
        """Approve selected commissions"""
        try:
            from models import Commission
            from app import db
            
            count = 0
            for commission_id in ids:
                commission = Commission.query.get(commission_id)
                if commission and commission.status == 'pending':
                    commission.status = 'approved'
                    commission.commission_available_date = datetime.now()
                    count += 1
            
            db.session.commit()
            flash(f'Successfully approved {count} commissions.')
            logger.info(f"Admin approved {count} commissions")
        except Exception as e:
            logger.error(f"Error approving commissions: {str(e)}")
            flash(f'Error approving commissions: {str(e)}', 'error')
    
    @action('reject', 'Reject', 'Are you sure you want to reject the selected commissions?')
    def reject_commission(self, ids):
        """Reject selected commissions"""
        try:
            from models import Commission
            from app import db
            
            count = 0
            for commission_id in ids:
                commission = Commission.query.get(commission_id)
                if commission and commission.status in ['pending', 'approved']:
                    commission.status = 'rejected'
                    count += 1
            
            db.session.commit()
            flash(f'Successfully rejected {count} commissions.')
            logger.info(f"Admin rejected {count} commissions")
        except Exception as e:
            logger.error(f"Error rejecting commissions: {str(e)}")
            flash(f'Error rejecting commissions: {str(e)}', 'error')
    
    @action('process_payouts', 'Process Payouts', 'Are you sure you want to process payouts for the selected commissions? This will initiate PayPal payouts.')
    def process_payouts(self, ids):
        """Process payouts for selected commissions"""
        try:
            from models import Commission, Affiliate
            from app import db
            
            # Group commissions by affiliate
            affiliate_commissions = {}
            for commission_id in ids:
                commission = Commission.query.get(commission_id)
                if not commission or commission.status != 'approved':
                    continue
                
                affiliate_id = commission.affiliate_id
                if affiliate_id not in affiliate_commissions:
                    affiliate_commissions[affiliate_id] = []
                
                affiliate_commissions[affiliate_id].append(commission)
            
            # Process each affiliate payout
            results = {}
            for affiliate_id, commissions in affiliate_commissions.items():
                # Get the affiliate
                affiliate = Affiliate.query.get(affiliate_id)
                if not affiliate or not affiliate.paypal_email:
                    flash(f'Affiliate {affiliate_id} has no PayPal email address.', 'error')
                    continue
                
                # Calculate the total amount
                total_amount = sum(commission.commission_amount for commission in commissions)
                
                # Process the payout
                payout_result = process_paypal_payouts([
                    {
                        'affiliate_id': affiliate_id,
                        'email': affiliate.paypal_email,
                        'amount': total_amount,
                        'commission_ids': [commission.id for commission in commissions]
                    }
                ])
                
                if payout_result and 'batch_id' in payout_result:
                    batch_id = payout_result['batch_id']
                    results[affiliate_id] = batch_id
                    
                    # Update the commissions
                    for commission in commissions:
                        commission.status = 'paid'
                        commission.payout_batch_id = batch_id
                else:
                    flash(f'Failed to process payout for affiliate {affiliate_id}.', 'error')
            
            db.session.commit()
            
            if results:
                flash(f'Successfully processed payouts for {len(results)} affiliates. Batch IDs: {results}')
                logger.info(f"Admin processed payouts for {len(results)} affiliates")
            else:
                flash('No payouts were processed.', 'warning')
                
        except Exception as e:
            logger.error(f"Error processing payouts: {str(e)}")
            flash(f'Error processing payouts: {str(e)}', 'error')

class UserModelView(ModelView, SecureBaseView):
    """User management view"""
    column_list = ['id', 'username', 'email', 'created_at']
    column_searchable_list = ['email', 'username']
    column_filters = ['created_at']
    column_default_sort = ('created_at', True)
    can_create = False  # Users are created through registration/Google Auth
    can_edit = True     # Allow editing for account management

class AffiliateModelView(ModelView, SecureBaseView):
    """Affiliate management view"""
    column_list = [
        'id', 'name', 'email', 'paypal_email', 'referral_code', 
        'status', 'terms_agreed_at', 'created_at'
    ]
    
    column_filters = ['status', 'created_at']
    column_searchable_list = ['email', 'paypal_email']
    column_default_sort = ('created_at', True)
    
    # Allow editing but not direct creation of affiliates
    can_create = False  # Affiliates are created through the regular registration flow
    can_edit = True     # Allow editing of affiliate details

class UserTokenUsageView(ModelView, SecureBaseView):
    """User token usage analytics view"""
    can_create = False
    can_edit = False
    can_delete = False
    
    def get_query(self):
        """Override query to show aggregated token usage data"""
        from models import Usage, User
        from app import db
        
        # Build a subquery to summarize token usage
        return (
            db.session.query(
                Usage.user_id.label('user_id'),
                User.email.label('email'),
                func.sum(Usage.input_tokens + Usage.output_tokens).label('total_credits'),
                func.max(Usage.timestamp).label('last_activity')
            )
            .join(User, Usage.user_id == User.id)
            .group_by(Usage.user_id, User.email)
            .order_by(desc('total_credits'))
        )
    
    def get_count_query(self):
        """Override count query to match the main query"""
        from models import Usage
        from app import db
        
        return (
            db.session.query(func.count(func.distinct(Usage.user_id)))
        )
    
    column_list = ['user_id', 'email', 'total_credits', 'last_activity']
    
    column_formatters = {
        'total_credits': lambda v, c, m, p: '{:,}'.format(m.total_credits) if m.total_credits else '0'
    }
    
    column_default_sort = ('total_credits', True)
    
    column_labels = {
        'user_id': 'User ID',
        'email': 'Email',
        'total_credits': 'Total Credits Used',
        'last_activity': 'Last Activity'
    }

class PopularModelsView(ModelView, SecureBaseView):
    """Popular models analytics view"""
    can_create = False
    can_edit = False
    can_delete = False
    
    def get_query(self):
        """Override query to show aggregated model usage data"""
        from models import Usage
        from app import db
        
        # Build a query to summarize model usage
        return (
            db.session.query(
                Usage.model_id.label('model_id'),
                func.count(Usage.id).label('usage_count'),
                func.sum(Usage.input_tokens + Usage.output_tokens).label('total_credits'),
                func.max(Usage.timestamp).label('last_used')
            )
            .group_by(Usage.model_id)
            .order_by(desc('usage_count'))
        )
    
    def get_count_query(self):
        """Override count query to match the main query"""
        from models import Usage
        from app import db
        
        return (
            db.session.query(func.count(func.distinct(Usage.model_id)))
        )
    
    column_list = ['model_id', 'usage_count', 'total_credits', 'last_used']
    
    column_formatters = {
        'total_credits': lambda v, c, m, p: '{:,}'.format(m.total_credits) if m.total_credits else '0',
        'usage_count': lambda v, c, m, p: '{:,}'.format(m.usage_count) if m.usage_count else '0'
    }
    
    column_default_sort = ('usage_count', True)
    
    column_labels = {
        'model_id': 'Model ID',
        'usage_count': 'Usage Count',
        'total_credits': 'Total Credits Used',
        'last_used': 'Last Used'
    }

def create_admin(app, db):
    """
    Create and initialize the admin interface for the application.
    
    Args:
        app: Flask application instance
        db: SQLAlchemy database instance
    
    Returns:
        Admin: The initialized Flask-Admin instance
    """
    # Import models only after app context is established
    with app.app_context():
        from models import User, Affiliate, Commission, Usage
        
        # Create admin instance
        admin = Admin(
            app, 
            name='GloriaMundo Admin',
            template_mode='bootstrap3',
            index_view=SecureAdminIndexView(name='Dashboard', url='/admin'),
            base_template='admin/master.html'
        )
        
        # Add views
        admin.add_view(UserModelView(User, db.session, name='Users', category='User Management'))
        admin.add_view(AffiliateModelView(Affiliate, db.session, name='Affiliates', category='Affiliate System'))
        admin.add_view(CommissionModelView(Commission, db.session, name='Commissions', category='Affiliate System'))
        admin.add_view(UserTokenUsageView(None, db.session, name='User Token Usage', category='Analytics'))
        admin.add_view(PopularModelsView(None, db.session, name='Popular Models', category='Analytics'))
        
        # Simple diagnostic routes
        @app.route('/admin-home')
        def admin_home():
            """Admin home page that checks access"""
            if current_user.is_authenticated:
                admin_emails = os.environ.get('ADMIN_EMAILS', 'andy@sentigral.com').split(',')
                is_admin = current_user.email in admin_emails
                if is_admin:
                    return redirect('/admin')
                return f'Access denied. {current_user.email} is not an admin. Admin users: {admin_emails}'
            return 'Please log in to access the admin dashboard'
        
        @app.route('/admin-check')
        def admin_check():
            """Diagnostic page to check admin access"""
            if not current_user.is_authenticated:
                return '<h1>Not logged in</h1><p>Please log in to check admin access.</p>'
            
            admin_emails = os.environ.get('ADMIN_EMAILS', 'andy@sentigral.com').split(',')
            is_admin = current_user.email in admin_emails
            
            return f"""
            <h1>Admin Check</h1>
            <p>Logged in as: {current_user.email}</p>
            <p>Admin emails: {admin_emails}</p>
            <p>Is admin: {is_admin}</p>
            <p><a href="/admin">Admin Dashboard</a></p>
            """
        
        @app.route('/admin-direct')
        def admin_direct():
            """Direct route to admin dashboard as a fallback"""
            return redirect('/admin')
            
        logger.info("Admin interface created successfully")
        return admin

@expose('/admin')
def admin_index():
    """Redirect to admin dashboard"""
    return redirect('/admin')