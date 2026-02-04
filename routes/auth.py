"""
Authentication routes blueprint
Handles login, logout, OAuth, and authentication checks
"""
import logging
import bcrypt
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from flask_login import login_user, login_required, logout_user, current_user
from models import User

# Create blueprint
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/', methods=['GET', 'POST'])
def index():
    logging.debug(f"Index accessed: authenticated={current_user.is_authenticated}")
    if not current_user.is_authenticated:
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']
            logging.debug(f"Login attempt: email={email}")
            user = User.query.filter_by(email=email).first()
            if user and bcrypt.checkpw(password.encode(), user.password.encode()):
                login_user(user)
                logging.debug("Login successful")
                return jsonify({'authenticated': True}), 200
            logging.debug("Login failed: Invalid email or password")
            return jsonify({'authenticated': False, 'message': 'Invalid email or password'}), 401
        return render_template('index.html')
    logging.debug("User is already authenticated")
    return render_template('index.html', email=current_user.email)

@auth_bp.route('/check_auth')
def check_auth():
    logging.debug(f"Authenticated: {current_user.is_authenticated}")
    return jsonify({
        'authenticated': current_user.is_authenticated,
        'email': current_user.email if current_user.is_authenticated else None
    }), 200

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        if current_user.is_authenticated:
            return jsonify({'authenticated': True}), 200

        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and bcrypt.checkpw(password.encode(), user.password.encode()):
            login_user(user)
            return jsonify({'authenticated': True}), 200

        return jsonify({'authenticated': False, 'message': 'Invalid email or password'}), 401
    except Exception as e:
        logging.error(f"Error in /login: {e}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Logout route - imports clear_game to avoid circular dependency"""
    from app import clear_game
    # Clear the user's game instance before logging out
    clear_game()
    logout_user()
    session.clear()  # Clear the session
    return jsonify({'message': 'Logged out successfully'}), 200
