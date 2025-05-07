"""
Forms for the GloriaMundo Chat Application.
Contains Flask-WTF form classes for various parts of the application.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField, EmailField
from wtforms.validators import DataRequired, Email, Optional

class AgreeToTermsForm(FlaskForm):
    """Form for agreeing to the affiliate terms and conditions."""
    # Field must match the HTML name attribute in tell_friend_tab.html
    agree_to_terms = BooleanField(
        'I have read and agree to the Affiliate Terms & Conditions',
        validators=[DataRequired()]
    )
    paypal_email = EmailField(
        'Your PayPal Email for Payouts (Optional)',
        validators=[Optional(), Email()]
    )
    # No submit field needed as it's already in the template

class UpdatePayPalEmailForm(FlaskForm):
    """Form for updating the PayPal email address."""
    # Field must match the HTML name attribute in tell_friend_tab.html
    paypal_email = EmailField(
        'PayPal Email',
        validators=[DataRequired(), Email()]
    )
    # No submit field needed as it's already in the template