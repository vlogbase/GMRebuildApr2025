import json
import os
import logging

import requests
from flask import Blueprint, current_app, redirect, request, url_for
from flask_login import login_required, login_user, logout_user
from oauthlib.oauth2 import WebApplicationClient

# Create logger for this module
logger = logging.getLogger(__name__)

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

    # Import here to avoid circular dependency
    from app import db
    from models import User
    from sqlalchemy.exc import IntegrityError
    from datetime import datetime
    
    try:
        # Get Google's unique sub (subject) identifier - this is the most reliable way to identify a Google user
        google_id = userinfo.get('sub')
        users_picture = userinfo.get('picture')
        
        # STEP 1: Try to find the user by their Google ID first (most reliable method)
        user = User.query.filter_by(google_id=google_id).first()
        
        # STEP 2: If not found by Google ID, try to find by email (migration case)
        if not user:
            user = User.query.filter_by(email=users_email).first()
            
            # If found by email but not Google ID, it's probably a user from the old system
            if user:
                logger.info(f"Found existing user by email {users_email} - linking Google ID {google_id}")
                # Update the existing user with the Google ID for future logins
                user.google_id = google_id
                user.profile_picture = users_picture
                db.session.commit()
                logger.info(f"Successfully linked Google ID to existing user: {user.id}")
            else:
                # This is a genuinely new user
                try:
                    # Try to create username from Google name, handle uniqueness carefully
                    base_username = users_name.lower().replace(' ', '_')
                    username = base_username
                    
                    # Check if username exists already and modify if needed
                    username_exists = User.query.filter_by(username=username).first()
                    attempt = 1
                    
                    # If username exists, append a number until we find a unique one
                    while username_exists and attempt < 100:
                        username = f"{base_username}_{attempt}"
                        username_exists = User.query.filter_by(username=username).first()
                        attempt += 1
                    
                    if attempt >= 100:
                        # Extremely unlikely, but just in case
                        username = f"{base_username}_{int(datetime.utcnow().timestamp())}"
                        
                    # Create new user with Google ID
                    logger.info(f"Creating new user for {users_email} with Google ID {google_id}")
                    user = User(
                        username=username,
                        email=users_email,
                        google_id=google_id,
                        profile_picture=users_picture
                    )
                    db.session.add(user)
                    db.session.commit()
                    logger.info(f"New user created with ID: {user.id}")
                except IntegrityError as ie:
                    # Handle database constraints violation explicitly
                    db.session.rollback()
                    logger.error(f"Database integrity error creating user: {ie}")
                    
                    # Check if it's a duplicate email or username
                    existing_email = User.query.filter_by(email=users_email).first()
                    if existing_email:
                        logger.warning(f"Attempted to create user with existing email: {users_email}")
                        return "Authentication error: Email already exists in system.", 400
                    
                    return "Authentication failed due to database constraints. Please try again.", 500
        else:
            # User was found by Google ID - regular login case
            logger.info(f"Existing user logged in via Google: {user.username} ({user.id})")
        
        # Update last login time
        user.last_login_at = datetime.utcnow()
        db.session.commit()
        
    except Exception as e:
        logger.error(f"Error in Google authentication: {e}")
        return "Authentication error. Please try again later.", 500

    login_user(user)

    return redirect(url_for("index"))


@google_auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))