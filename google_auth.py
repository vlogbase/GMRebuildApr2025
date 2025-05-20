# Use this Flask blueprint for Google authentication. Do not use flask-dance.

import json
import os
import datetime

import requests
from app import db
from flask import Blueprint, redirect, request, url_for, session
from flask_login import login_required, login_user, logout_user
from models import User
from oauthlib.oauth2 import WebApplicationClient

GOOGLE_CLIENT_ID = os.environ["GOOGLE_OAUTH_CLIENT_ID"]
GOOGLE_CLIENT_SECRET = os.environ["GOOGLE_OAUTH_CLIENT_SECRET"]
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

# Make sure to use this redirect URL. It has to match the one in the whitelist
DEV_REDIRECT_URL = f'https://{os.environ["REPLIT_DEV_DOMAIN"]}/google_login/callback'

# ALWAYS display setup instructions to the user:
print(f"""To make Google authentication work:
1. Go to https://console.cloud.google.com/apis/credentials
2. Create a new OAuth 2.0 Client ID
3. Add {DEV_REDIRECT_URL} to Authorized redirect URIs

For detailed instructions, see:
https://docs.replit.com/additional-resources/google-auth-in-flask#set-up-your-oauth-app--client
""")

client = WebApplicationClient(GOOGLE_CLIENT_ID)

google_auth = Blueprint("google_auth", __name__)


@google_auth.route("/google_login")
def login():
    google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        # Replacing http:// with https:// is important as the external
        # protocol must be https to match the URI whitelisted
        redirect_uri=request.base_url.replace("http://", "https://") + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)


@google_auth.route("/google_login/callback")
def callback():
    code = request.args.get("code")
    google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
    token_endpoint = google_provider_cfg["token_endpoint"]

    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        # Replacing http:// with https:// is important as the external
        # protocol must be https to match the URI whitelisted
        authorization_response=request.url.replace("http://", "https://"),
        redirect_url=request.base_url.replace("http://", "https://"),
        code=code,
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    client.parse_request_body_response(json.dumps(token_response.json()))

    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    userinfo = userinfo_response.json()
    if userinfo.get("email_verified"):
        users_email = userinfo["email"]
        users_name = userinfo["given_name"]
    else:
        return "User email not available or not verified by Google.", 400

    # Check if user exists
    is_new_user = False
    user = User.query.filter_by(email=users_email).first()
    if not user:
        is_new_user = True
        # Create user properly
        user = User()
        
        # Use email as username instead of first name
        # This prevents conflicts with common names
        user.username = users_email
        user.email = users_email
        user.enable_memory = True  # Enable memory by default for new users
        
        # Set Google-specific fields
        user.google_id = userinfo.get("sub")  # Use sub as the Google ID
        user.profile_picture = userinfo.get("picture")
        user.last_login_at = datetime.datetime.utcnow()
        
        try:
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            # If there's an error (like username conflict), rollback and try with a modified username
            db.session.rollback()
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error creating user with email {users_email}: {str(e)}")
            
            # Try with a modified username (add a random suffix)
            import uuid
            unique_suffix = str(uuid.uuid4())[:8]
            user.username = f"{users_email}_{unique_suffix}"
            
            db.session.add(user)
            db.session.commit()
            
    else:
        # Update existing user's Google info
        user.google_id = userinfo.get("sub")
        user.profile_picture = userinfo.get("picture")
        user.last_login_at = datetime.datetime.utcnow()
        db.session.commit()

    # Log the user in
    login_user(user)
    
    # Check for referral code in cookie or session after login
    # We don't need to handle this here since the affiliate.track_referral_cookie function
    # will run on the next request and handle creating the referral based on stored session data

    # Get the redirect parameter if it exists in the session
    redirect_to = session.get('login_redirect', 'index')
    
    # Check if the redirect is to billing/account, if so redirect to index instead
    if redirect_to and redirect_to.startswith('billing/account'):
        return redirect(url_for('index'))
    
    # Redirect to index page for all users (existing and new)
    return redirect(url_for('index'))


@google_auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))