"""
Admin Module for GloriaMundo Chatbot

This module handles admin routes and views using Flask-Admin.
It provides a secure admin interface for managing the affiliate system.
"""
import os
from datetime import datetime

from flask import flash, redirect, request, url_for
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.actions import action
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user, login_required

from app import app, db
from models import Affiliate, Commission, CommissionStatus, OpenRouterModel, Transaction, User, Usage
from affiliate import is_admin
# Try to import the paypal_payouts module
try:
    from paypal_payouts import process_payouts as process_paypal_payouts
except ImportError:
    # Define a dummy function if the module isn't available
    def process_paypal_payouts(affiliate_commissions):
        """Dummy function if paypal_payouts module isn't available"""
        return {"success": False, "error": "PayPal Payouts module not available"}


class SecureBaseView:
    """Base view with security features for all admin views"""

    def is_accessible(self):
        """Only allow access to admin users (email: andy@sentigral.com)"""
        return current_user.is_authenticated and is_admin()

    def inaccessible_callback(self, name, **kwargs):
        """Redirect to login page if user doesn't have access"""
        return redirect(url_for('login', next=request.url))


class SecureAdminIndexView(AdminIndexView, SecureBaseView):
    """Secure index view for admin panel"""

    @expose('/')
    def index(self):
        """Admin dashboard home page with overview statistics"""
        # Gather statistics for the dashboard
        stats = {
            'total_users': User.query.count(),
            'total_affiliates': Affiliate.query.count(),
            'pending_commissions': Commission.query.filter_by(status=CommissionStatus.HELD.value).count(),
            'approved_commissions': Commission.query.filter_by(status=CommissionStatus.APPROVED.value).count(),
            'total_commission_amount': sum([c.commission_amount for c in Commission.query.filter(
                Commission.status.in_([CommissionStatus.HELD.value, CommissionStatus.APPROVED.value, CommissionStatus.PAID.value])
            ).all()]),
        }
        return self.render('admin/index.html', stats=stats)


class CommissionModelView(ModelView, SecureBaseView):
    """Commission management view"""

    # Display columns
    column_list = [
        'id', 'affiliate.email', 'commission_level', 'purchase_amount_base', 
        'commission_amount', 'status', 'commission_earned_date', 
        'commission_available_date', 'payout_batch_id'
    ]

    # Formatters for better display
    column_formatters = {
        'purchase_amount_base': lambda v, c, m, p: f'£{m.purchase_amount_base:.2f}',
        'commission_amount': lambda v, c, m, p: f'£{m.commission_amount:.2f}'
    }

    # Sorting and filtering
    column_default_sort = ('commission_available_date', True)
    column_filters = ['status', 'commission_available_date', 'commission_level']
    
    # Custom actions for commission management
    actions = ['approve_commission', 'reject_commission', 'process_payouts']

    def _get_affiliate_email(view, context, model, name):
        """Get the affiliate email for display"""
        if model.affiliate:
            return model.affiliate.email
        return None

    column_formatters = {
        'affiliate.email': _get_affiliate_email,
        'purchase_amount_base': lambda v, c, m, p: f'£{m.purchase_amount_base:.2f}',
        'commission_amount': lambda v, c, m, p: f'£{m.commission_amount:.2f}'
    }

    @action('approve_commission', 'Approve Commission', 
            'Are you sure you want to approve the selected commissions?')
    def approve_commission(self, ids):
        """Approve selected commissions"""
        now = datetime.utcnow()
        try:
            query = Commission.query.filter(Commission.id.in_(ids))
            count = 0
            
            for commission in query.all():
                # Only approve commissions that are in HELD status and past their available date
                if (commission.status == CommissionStatus.HELD.value and 
                    commission.commission_available_date <= now):
                    commission.status = CommissionStatus.APPROVED.value
                    count += 1
            
            db.session.commit()
            flash(f'{count} commissions were successfully approved.')
        except Exception as ex:
            db.session.rollback()
            flash(f'Error approving commissions: {str(ex)}', 'error')

    @action('reject_commission', 'Reject Commission', 
            'Are you sure you want to reject the selected commissions?')
    def reject_commission(self, ids):
        """Reject selected commissions"""
        try:
            query = Commission.query.filter(Commission.id.in_(ids))
            count = 0
            
            for commission in query.all():
                # Can only reject commissions that are in HELD or APPROVED status
                if commission.status in [CommissionStatus.HELD.value, CommissionStatus.APPROVED.value]:
                    commission.status = CommissionStatus.REJECTED.value
                    count += 1
            
            db.session.commit()
            flash(f'{count} commissions were successfully rejected.')
        except Exception as ex:
            db.session.rollback()
            flash(f'Error rejecting commissions: {str(ex)}', 'error')

    @action('process_payouts', 'Process Payouts', 
            'Are you sure you want to process payouts for the selected commissions?')
    def process_payouts(self, ids):
        """Process payouts for selected commissions"""
        try:
            # Get commissions that are approved
            commissions = Commission.query.filter(
                Commission.id.in_(ids),
                Commission.status == CommissionStatus.APPROVED.value
            ).all()
            
            if not commissions:
                flash('No eligible commissions found for payout.', 'error')
                return
                
            # Group commissions by affiliate
            affiliate_commissions = {}
            for commission in commissions:
                if not commission.affiliate.paypal_email:
                    flash(f'Affiliate ID {commission.affiliate_id} does not have a PayPal email address.', 'error')
                    continue
                    
                if commission.affiliate_id not in affiliate_commissions:
                    affiliate_commissions[commission.affiliate_id] = {
                        'paypal_email': commission.affiliate.paypal_email,
                        'commissions': [],
                        'total_amount': 0
                    }
                
                affiliate_commissions[commission.affiliate_id]['commissions'].append(commission)
                affiliate_commissions[commission.affiliate_id]['total_amount'] += commission.commission_amount
            
            # Process payouts
            if not affiliate_commissions:
                flash('No valid affiliates found for payout.', 'error')
                return
                
            payout_results = process_paypal_payouts(affiliate_commissions)
            
            if payout_results.get('success'):
                flash(f'Successfully processed payouts. Batch ID: {payout_results.get("batch_id")}')
            else:
                flash(f'Error processing payouts: {payout_results.get("error")}', 'error')
                
        except Exception as ex:
            flash(f'Error processing payouts: {str(ex)}', 'error')


class AffiliateModelView(ModelView, SecureBaseView):
    """Affiliate management view"""
    
    # Display columns
    column_list = [
        'id', 'name', 'email', 'paypal_email', 'referral_code', 
        'status', 'terms_agreed_at', 'created_at'
    ]
    
    # Filters
    column_filters = ['status', 'created_at']
    
    # Make email and paypal_email searchable
    column_searchable_list = ['email', 'paypal_email']
    
    # Default sort
    column_default_sort = ('created_at', True)


class UserTokenUsageView(ModelView, SecureBaseView):
    """User token usage analytics view"""
    
    # Make this view read-only
    can_create = False
    can_edit = False
    can_delete = False
    
    # Custom SQL query for aggregated data
    def get_query(self):
        return self.session.query(
            User.id.label('user_id'),
            User.email.label('email'),
            db.func.sum(Usage.credits_used).label('total_credits'),
            db.func.max(Usage.created_at).label('last_activity')
        ).outerjoin(Usage, User.id == Usage.user_id).group_by(User.id, User.email)
    
    def get_count_query(self):
        return self.session.query(db.func.count(db.func.distinct(User.id)))
    
    # Display columns
    column_list = ['user_id', 'email', 'total_credits', 'last_activity']
    
    # Formatters
    column_formatters = {
        'total_credits': lambda v, c, m, p: '{:,}'.format(m.total_credits) if m.total_credits else '0'
    }
    
    # Sorting
    column_default_sort = ('total_credits', True)
    
    # Rename the view
    column_labels = {
        'user_id': 'User ID',
        'email': 'Email',
        'total_credits': 'Total Credits Used',
        'last_activity': 'Last Activity'
    }


class PopularModelsView(ModelView, SecureBaseView):
    """Popular models analytics view"""
    
    # Make this view read-only
    can_create = False
    can_edit = False
    can_delete = False
    
    # Custom SQL query for aggregated data
    def get_query(self):
        return self.session.query(
            Usage.model_id.label('model_id'),
            db.func.count(Usage.id).label('usage_count'),
            db.func.sum(Usage.credits_used).label('total_credits'),
            db.func.max(Usage.created_at).label('last_used')
        ).group_by(Usage.model_id)
    
    def get_count_query(self):
        return self.session.query(db.func.count(db.func.distinct(Usage.model_id)))
    
    # Display columns
    column_list = ['model_id', 'usage_count', 'total_credits', 'last_used']
    
    # Formatters
    column_formatters = {
        'total_credits': lambda v, c, m, p: '{:,}'.format(m.total_credits) if m.total_credits else '0',
        'usage_count': lambda v, c, m, p: '{:,}'.format(m.usage_count) if m.usage_count else '0'
    }
    
    # Sorting
    column_default_sort = ('usage_count', True)
    
    # Rename the view
    column_labels = {
        'model_id': 'Model ID',
        'usage_count': 'Usage Count',
        'total_credits': 'Total Credits Used',
        'last_used': 'Last Used'
    }


# Create admin interface
admin = Admin(
    app, 
    name='GloriaMundo Admin', 
    url='/gm-admin',
    endpoint='gm_admin',
    template_mode='bootstrap3',
    index_view=SecureAdminIndexView(name='Dashboard')
)

# Add views
admin.add_view(CommissionModelView(Commission, db.session, name='Commissions'))
admin.add_view(AffiliateModelView(Affiliate, db.session, name='Affiliates'))
admin.add_view(UserTokenUsageView(User, db.session, name='User Token Usage', endpoint='user_token_usage'))
admin.add_view(PopularModelsView(Usage, db.session, name='Popular Models', endpoint='popular_models'))

# Create a custom admin template for the index page
@app.route('/admin')
@login_required
def admin_index():
    """Redirect to admin dashboard"""
    if not is_admin():
        flash('You do not have permission to access the admin area.', 'error')
        return redirect(url_for('index'))
    return redirect(url_for('gm_admin.index'))