"""
Main Flask application
Handles initialization, configuration, and blueprint registration
"""
import os
import logging
from flask import Flask, session, request, redirect
from authlib.integrations.flask_client import OAuth
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

from game_logic import developmentGame
from models import db, User

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object('config.Config')

# Handle missing DATABASE_URL
database_url = os.environ.get('DATABASE_URL')
if database_url:
    database_url = database_url.replace("postgres://", "postgresql://")
else:
    database_url = 'sqlite:///app.db'

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)

# Redirect non-www to www
@app.before_request
def redirect_to_www():
    """Redirect non-www requests to www subdomain"""
    base_domain = os.getenv('BASE_DOMAIN', '')
    if base_domain and request.host == base_domain:
        return redirect(f'https://www.{base_domain}{request.path}', code=301)

# Initialize Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.index'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# OAuth setup
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    access_token_url='https://oauth2.googleapis.com/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_callback_url=os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:5001/authorize'),
    client_kwargs={
        'scope': 'openid profile email',
        'token_endpoint_auth_method': 'client_secret_post',
        'token_placement': 'header',
        'prompt': 'select_account'
    },
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    issuer='https://accounts.google.com'
)

# Per-user game storage using sessions
# Store game instances in a dictionary keyed by user ID
_game_instances = {}

def get_game():
    """Get or create a game instance for the current user"""
    if not current_user.is_authenticated:
        # For unauthenticated users, use a temporary session-based game
        # (This shouldn't happen in practice since routes require login)
        session_id = session.get('temp_session_id')
        if not session_id:
            import uuid
            session_id = str(uuid.uuid4())
            session['temp_session_id'] = session_id
        user_key = f"temp_{session_id}"
    else:
        # For authenticated users, use their user ID
        user_key = f"user_{current_user.id}"

    # Create game instance if it doesn't exist for this user
    if user_key not in _game_instances:
        _game_instances[user_key] = developmentGame()
        logging.debug(f"Created new game instance for {user_key}")

    return _game_instances[user_key]

def clear_game():
    """Clear the game instance for the current user"""
    if not current_user.is_authenticated:
        session_id = session.get('temp_session_id')
        if session_id:
            user_key = f"temp_{session_id}"
        else:
            return
    else:
        user_key = f"user_{current_user.id}"

    if user_key in _game_instances:
        del _game_instances[user_key]
        logging.debug(f"Cleared game instance for {user_key}")

# Register blueprints
from routes.auth import auth_bp
from routes.oauth import oauth_bp
from routes.game import game_bp
from routes.settings import settings_bp
from routes.data import data_bp
from routes.scenarios import scenarios_bp

app.register_blueprint(auth_bp)
app.register_blueprint(oauth_bp)
app.register_blueprint(game_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(data_bp)
app.register_blueprint(scenarios_bp)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)
