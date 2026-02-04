"""
OAuth routes blueprint
Handles Google OAuth authentication flow
"""
import logging
from flask import Blueprint, redirect, url_for, jsonify
from flask_login import login_user
from models import User

# Create blueprint
oauth_bp = Blueprint('oauth', __name__)

@oauth_bp.route('/login/google')
def login_google():
    """Initiate Google OAuth flow"""
    from app import google  # Import here to avoid circular dependency
    redirect_uri = url_for('oauth.authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@oauth_bp.route('/authorize')
def authorize():
    """Handle OAuth callback from Google"""
    from app import google  # Import here to avoid circular dependency
    try:
        token = google.authorize_access_token()
        resp = google.get('https://www.googleapis.com/oauth2/v3/userinfo')
        user_info = resp.json()
        user = User.get_or_create(user_info)
        login_user(user)
        return redirect(url_for('auth.index'))
    except Exception as e:
        logging.error(f"Error during OAuth authorization: {e}")
        return jsonify({'error': str(e)}), 500
