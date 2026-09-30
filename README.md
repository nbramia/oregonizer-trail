# Oregonizer Trail

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

## Why This Exists

This game aims to help you get a feel for the difficult decisions that people across an organization are making each day.

**Oregonizer Trail aims to make tradeoffs more real.** Each person and each team juggle different incentives, different priorities, and different constraints—and each of us are primarily aware of our own (while being less viscerally aware of those of others). This can be especially true in an organization with both highly technical staff and staff who lead less technical areas like account management, comms, operations, etc.

**It requires a lot of empathy** to navigate the cross-functional set of decisions that go into each program we run. This is difficult to learn, because most of us are primarily aware of one type of priority or metric (and less tuned into the others)—while many decisions ultimately come down to yes or no, on specific questions.

**The key insight for successful players** will be that very few of these questions have an objectively-correct answer. Instead, winning will look like intuiting the likely effect of a given choice on your metrics and making the choice whose downsides you're prepared to accept at that moment, as you try to keep your head above water. It's all situational.

You'll also notice that effects of different choices have an element of randomness (sometimes effects are larger than at other times), and as the difficulty increases, those effect sizes grow. You don't always know how a decision is going to turn out or the effect it's going to have.

Similar to the classic 90's [Oregon Trail](https://www.visitoregon.com/the-oregon-trail-game-online/) video game, you'll be faced with difficult decisions, and your choices will affect your chance of success. Also similar to the Oregon Trail, sometimes you won't have a choice: you'll be presented with something outside your control, which you'll just have to accept.

---

## Overview

A web-based simulation game where players manage critical metrics through decision-making scenarios while navigating external events, all in a retro terminal-style interface.

## Table of Contents

- [Core Features](#core-features)
- [Game Rules and Behavior](#game-rules-and-behavior)
- [Tech Stack](#tech-stack)
- [Architecture and Code Organization](#architecture-and-code-organization)
- [State Management](#state-management)
- [User Management and Data](#user-management-and-data)
- [Database Schema](#database-schema)
- [Build and Deployment](#build-and-deployment)
- [Development Workflow](#development-workflow)
- [Environment Configuration](#environment-configuration)
- [Gameplay Examples](#gameplay-examples)
- [Scoring System](#scoring-system)
- [Game Constraints](#game-constraints)
- [Code Patterns and Standards](#code-patterns-and-standards)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Core Features

### Game Modes

The application supports multiple game modes, each with unique scenarios. Available modes are configured in `mode_config.py`.

**Current Modes**:
- **Product Development**: Scenarios focused on feature prioritization, technical debt, team capacity, and product roadmap decisions
- **Partnership & Support**: Scenarios centered on customer relationships, support operations, renewal strategies, and stakeholder management
- **Movement Labs**: Scenarios focused on movement building, community engagement, and organizational growth

**Configuring Modes**:
To enable/disable modes, edit `mode_config.py`:

```python
MODES = [
    {
        'name': 'Product Development',
        'enabled': True,    # Set to False to hide this mode
        'default': True,    # This is the default mode on game start
        'description': '...'
    },
    # ... other modes
]
```

Changes take effect on next deployment. See [MODE_CONFIGURATION_GUIDE.md](MODE_CONFIGURATION_GUIDE.md) for complete documentation.

### Scenario Types
1. **Decision Scenarios (75% frequency)**: Present players with Yes/No choices that affect metrics differently based on their selection
2. **Informational Scenarios (25% frequency)**: External events that happen to the player regardless of choice, reflecting real-world unpredictability

### Difficulty Levels
- **Normal**: Starting metrics at 100, variation range 0.8-1.25x (80% to 125% of base effect)
- **Hard**: Starting metrics at 85 (tech debt at 75), variation range 1.0-1.4x
- **Crazy**: Starting metrics at 75 (tech debt at 50), variation range 1.1-1.6x

### Community Features
- **Scenario Creation**: Authenticated users can create custom scenarios with validation
- **Rating System**: Thumbs up/down ratings for both scenario text and response outcomes
- **Toggle Control**: Players can enable/disable community-submitted scenarios

### Authentication
- **Email/Password**: Traditional authentication with bcrypt password hashing
- **Google OAuth**: Single sign-on integration with dynamic redirect URI configuration

### User Statistics
- **High Score**: Automatically calculated and tracked based on difficulty, survival, and metrics
- **Games Played**: Total completed games (reached end state)
- **Games Started**: Games that reached Turn 2 or beyond
- **Last Played**: Timestamp of most recent game completion
- **Leaderboard**: Top 10 high scorers displayed in settings

## Game Rules and Behavior

### Core Metrics (Mode-Dependent)

Players must balance interconnected metrics that vary by game mode. All metrics are capped at 0-100 during gameplay.

**Product Development & Partnership & Support Modes**:

1. **Staff Retention** (0-100)
   - Reflects team morale, burnout, and retention
   - Affected by work-life balance decisions, deadline pressure, workload
   - Loss condition: ≤ 0 ("Too many key staff have left the organization...")

2. **Partner Retention** (0-100)
   - Measures existing customer satisfaction and renewal rates
   - Affected by product quality, support responsiveness, feature prioritization
   - Loss condition: ≤ 0 ("Too many partners have chosen not to renew...")

3. **Partner Growth** (0-100)
   - Tracks new customer acquisition and market expansion
   - Affected by new feature development, market positioning, reputation
   - Loss condition: ≤ 0 ("We're not making enough progress toward our vision...")

4. **Tech Debt** (0-100)
   - Represents platform stability, maintainability, and technical health
   - **Auto-decays** each turn by: `round((partner_growth + partner_retention) / 200)`
   - Higher partner activity = faster tech debt accumulation
   - Loss condition: ≤ 0 ("Tech debt has overwhelmed the platform...")

**Movement Labs Mode**:

1. **Staff Retention** (0-100) - Same as above

2. **Revenue** (0-100)
   - Tracks organizational financial sustainability
   - Loss condition: ≤ 0 ("Revenue has dried up...")

3. **Net Votes** (0-100)
   - Measures progress toward mission and impact goals
   - Loss condition: ≤ 0 ("We're not making enough progress toward our mission...")

4. **Tech Debt** (0-100)
   - **Auto-decays** each turn by: `round((revenue + net_votes) / 200)`
   - Loss condition: ≤ 0 ("Tech debt has overwhelmed the platform...")

### Turn Progression

Each turn follows this sequence:

1. **Turn counter increments**
2. **Tech debt auto-adjustment** (based on partner metrics)
3. **Scenario selection**:
   - 75% chance: Decision scenario from shuffled queue
   - 25% chance: Informational scenario from shuffled queue
   - Queues auto-refresh when exhausted (re-shuffled)
4. **Metric updates** (for informational scenarios) or player decision
5. **Status check** for win/loss conditions

### Metric Variation

All metric changes are modified by a difficulty-based variation range:
```python
actual_change = base_change * random.uniform(*variation_range)
```

This creates unpredictability where the same decision can have different magnitudes of effect.

### Win Conditions

Players win by achieving **either**:
1. **Survival Victory**: Reaching Turn 25 without any metric hitting ≤ 0
2. **Thriving Victory**: After Turn 10, having all non-tech_debt metrics at 100 (exactly)

### Loss Conditions

Game ends immediately when **any** metric drops to ≤ 0 with specific failure messages for each. If multiple metrics fail simultaneously, all failure messages are displayed separated by line breaks.

### Scenario Queue Management

- Decision and informational scenarios are loaded separately from the database
- Filtered by selected mode and community scenario toggle
- Shuffled on game initialization
- Scenarios pop from front of queue; queue refreshes when empty
- Prevents immediate repetition while ensuring variety

## Tech Stack

### Backend
- **Flask 3.0.3**: Web framework and routing
- **SQLAlchemy 2.0.31**: ORM for database operations
- **Flask-SQLAlchemy 3.1.1**: SQLAlchemy integration
- **Flask-Login 0.6.3**: Session management and authentication
- **Flask-Migrate**: Alembic-based database migrations
- **Flask-WTF 1.2.1**: CSRF protection for forms and AJAX requests
- **Bcrypt 3.2.0**: Password hashing (using `bcrypt.hashpw` and `bcrypt.checkpw`)
- **Authlib**: OAuth 2.0 client implementation for Google authentication
- **Python-dotenv 0.19.2**: Environment variable management

### Frontend
- **Vanilla JavaScript**: Single-page application logic (no framework)
- **Tailwind CSS 2.2.19** (CDN): Utility-first styling
- **Press Start 2P** (Google Fonts): Retro gaming font for headers
- **Font Awesome 6.0**: Icons for UI elements
- **Tenor Embed API**: Animated GIF integration for game states

### Database
- **PostgreSQL** (production via Neon, provisioned through the Vercel Marketplace)
- **SQLite** (local development fallback)
- **Psycopg2-binary 2.9.9**: PostgreSQL adapter

### Deployment
- **Vercel**: Serverless Python hosting (`vercel.json` sets the Flask preset)
- **Python 3.12**: Runtime (specified in `.python-version`)
- Live at https://oregonizertrail.vercel.app (the old oregonizertrail.org domain and Heroku app are retired)

## Architecture and Code Organization

### File Structure

```
oregonizer_trail/
├── app.py                      # Main Flask application and blueprint registration
├── game_logic.py               # Core game engine (developmentGame class)
├── models.py                   # SQLAlchemy models (User, Scenario, Rating)
├── config.py                   # Configuration class (database URI, secret key)
├── mode_config.py              # Game mode configuration and metrics
├── validation.py               # Input validation module for API endpoints
├── scenarios.py                # Legacy scenario definitions (class-based, mostly unused)
├── utilities.py                # Helper functions (password hashing)
├── requirements.txt            # Python dependencies
├── vercel.json                 # Vercel config (Flask framework preset)
├── .python-version             # Python version for Vercel
├── .vercelignore               # Files excluded from Vercel uploads
├── .env                        # Environment variables (not committed)
├── .env.example                # Environment variable template
├── routes/                     # Flask blueprint routes (modular organization)
│   ├── auth.py                # Email/password authentication routes
│   ├── oauth.py               # Google OAuth routes
│   ├── game.py                # Game state routes (reset, next_turn, end_game)
│   ├── settings.py            # Difficulty/mode/community settings routes
│   ├── data.py                # Data retrieval routes (leaderboard, modes, metrics)
│   └── scenarios.py           # Scenario creation and rating routes
├── migrations/                 # Alembic database migration scripts
├── templates/
│   └── index.html             # Single-page frontend application
├── static/
│   ├── js/
│   │   └── game.js            # Frontend game logic
│   └── [assets]               # Favicons, terms, privacy
├── scenarios_*.csv             # Mode-specific scenario data files
├── LICENSE                     # GPL v3 license
├── CONTRIBUTING.md             # Contribution guidelines
└── archive/                    # Archived utility scripts (user/scenario management)
```

### Core Architecture Patterns

#### 1. Per-User Game Instances (app.py:75-114)
```python
_game_instances = {}

def get_game():
    """Get or create a game instance for the current user"""
    if not current_user.is_authenticated:
        # Session-based game for unauthenticated users
        session_id = session.get('temp_session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            session['temp_session_id'] = session_id
        user_key = f"temp_{session_id}"
    else:
        # User ID-based game for authenticated users
        user_key = f"user_{current_user.id}"

    if user_key not in _game_instances:
        _game_instances[user_key] = developmentGame()

    return _game_instances[user_key]
```
- Each user gets their own independent `developmentGame` instance
- Game instances keyed by user ID (authenticated) or session ID (temp)
- **Supports concurrent multi-user play** - users don't interfere with each other
- Game instances cleared on logout to prevent memory leaks
- `clear_game()` function removes user's game instance when resetting

#### 2. Input Validation and Security (validation.py)
- **CSRF Protection**: Flask-WTF protects all POST/PUT/DELETE requests
- **Input Validation**: Comprehensive validation on all critical endpoints
  - `/set_difficulty`: Validates difficulty is one of ['Normal', 'Hard', 'Crazy']
  - `/end_game`: Validates turns_survived (0-1000), difficulty, all metrics (0-200)
  - `/create_scenario`: Validates name, mode, type, text, metrics JSON, response JSON
- **Mode-Aware Validation**: Metrics validated against current mode's metric list
- **Environment Variables**: OAuth credentials and secret key loaded from environment
- **Descriptive Errors**: Validation failures return 400 with clear error messages

#### 3. Database-Driven Scenarios
- Scenarios stored in PostgreSQL/SQLite, not hardcoded
- Loaded on game initialization/reset via SQLAlchemy queries
- Metrics and responses stored as JSON strings, deserialized at runtime
- Legacy `scenarios.py` contains class-based definitions (mostly for reference/import)

#### 4. JSON Metric Storage

**Decision Scenario Metrics** (app.py:428-442):
```python
metrics = {
    "yes": {
        "staff_retention": -35,
        "partner_growth": 0,
        "partner_retention": -15,
        "tech_debt": 20
    },
    "no": {
        "staff_retention": 25,
        "partner_growth": -15,
        "partner_retention": -10,
        "tech_debt": 0
    }
}
```

**Informational Scenario Metrics** (app.py:444-449):
```python
metrics = {
    "staff_retention": -20,
    "partner_growth": 10,
    "partner_retention": -5,
    "tech_debt": 15
}
```

#### 5. Frontend-Backend Communication
- RESTful JSON API endpoints
- Fetch API with CSRF token injection for all HTTP requests
- `fetchWithCSRF()` helper automatically adds X-CSRFToken header
- No page reloads; fully dynamic UI updates
- State managed in JavaScript `gameState` variable

#### 6. Authentication Flow

**Email/Password** (app.py:75-92):
1. POST to `/` with credentials
2. Bcrypt password verification
3. Flask-Login session creation
4. JSON response with authentication status

**Google OAuth** (app.py:121-140):
1. GET `/login/google` initiates OAuth flow
2. Google redirects to `/authorize`
3. Token exchange and user info fetch
4. User.get_or_create() auto-creates account
5. Flask-Login session creation

## State Management

### Game State (game_logic.py)

The `developmentGame` class maintains all game state with dynamic metrics based on mode:

```python
class developmentGame:
    def __init__(self):
        from mode_config import get_default_mode
        self.difficulty = "Normal"
        self.mode = get_default_mode()  # Dynamically set from mode_config.py
        self.variation_range = (0.8, 1.25)
        self.include_community_scenarios = False
        # Metrics - stored in dictionary, varies by mode
        self.metrics = {}  # e.g., {'staff_retention': 100, 'revenue': 100, ...}
        # State
        self.turns_survived = 0
        self.status = "developing"
        self.current_scenario = None
        # Scenario queues
        self.decision_scenarios = []
        self.informational_scenarios = []
        self.decision_scenarios_queue = []
        self.informational_scenarios_queue = []
```

**Dynamic Metrics System**:
- Metrics are stored in `self.metrics` dictionary
- Available metrics determined by current mode (via `mode_config.py`)
- Metrics automatically initialized based on difficulty level
- All metric changes clamped to 0-100 range during gameplay

### State Transitions

1. **Initialization**: `reset_game()` → sets initial values → loads scenarios
2. **Game Start**: First `next_turn()` call with `isFirstTurn=true`
3. **Mid-Game**: Repeated `next_turn()` → `handle_scenario()` → metric updates
4. **End State**: Win/loss condition met → `endGame()` → score calculation

### Session Management

- **Flask Session**: Server-side session storage for authenticated users
- **Flask-Login**: `current_user` proxy for accessing logged-in user
- **@login_required**: Decorator protecting authenticated-only routes
- **Session Clear**: Explicit `session.clear()` on logout (app.py:146)

### Frontend State (index.html:746)

```javascript
let gameState = "initial";  // States: "initial", "mid", "win", "failure"
let turnIncremented = false; // Prevents double-incrementing turns
```

## User Management and Data

### User Model (models.py:11-34)

```python
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(128), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=True)  # Nullable for OAuth users
    high_score = db.Column(db.Integer, default=0)
    games_played = db.Column(db.Integer, default=0)
    games_started = db.Column(db.Integer, default=0)
    last_game_played = db.Column(db.DateTime, default=None)
```

### User Statistics Tracking

**Games Started** (app.py:169-182):
- Increments when player reaches Turn 2
- Tracks user engagement beyond initial curiosity

**Games Played** (app.py:318):
- Increments on `/end_game` endpoint call
- Represents completed games (win or loss)

**High Score** (app.py:314-315):
- Automatically updates if new score exceeds previous
- Composite score calculation (see Scoring System)

**Last Game Played** (app.py:319):
- Timestamp of most recent game completion
- Uses `datetime.utcnow()`

### OAuth User Creation (models.py:23-34)

```python
@staticmethod
def get_or_create(user_info):
    email = user_info['email']
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(
            email=email,
            password=bcrypt.hashpw(user_info['sub'].encode(), bcrypt.gensalt()).decode()
        )
        db.session.add(user)
        db.session.commit()
    return user
```

## Database Schema

### Tables

#### User
| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | Primary Key |
| email | String(128) | Unique, Not Null |
| password | String(128) | Nullable (for OAuth) |
| high_score | Integer | Default: 0 |
| games_played | Integer | Default: 0 |
| games_started | Integer | Default: 0 |
| last_game_played | DateTime | Default: None |

#### Scenario
| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | Primary Key |
| name | String(128) | Unique, Not Null |
| mode | String(128) | Not Null |
| type | String(128) | Not Null ('decision' or 'informational') |
| text | Text | Not Null |
| metrics | Text | Not Null (JSON string) |
| response | Text | Nullable (JSON string, decision scenarios only) |
| community | Boolean | Default: False |

#### Rating
| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | Primary Key |
| user_id | Integer | Foreign Key → User.id, Not Null |
| scenario_id | Integer | Foreign Key → Scenario.id, Not Null |
| is_response | Boolean | Default: False |
| rating | Integer | Not Null (1 or -1) |
| submitted_at | DateTime | Default: datetime.utcnow |

### Relationships
- User ← (1:many) → Rating
- Scenario ← (1:many) → Rating

## Build and Deployment

### Local Development

1. **Install Dependencies**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure Environment**
Create `.env` file:
```
DATABASE_URL=postgresql://localhost/oregonizer_trail
GOOGLE_REDIRECT_URI=http://localhost:5001/authorize
```

3. **Initialize Database**
```bash
python create_db.py
flask db upgrade
python populate_scenarios.py  # Load scenario data
```

4. **Run Development Server**
```bash
python app.py
# Runs on http://0.0.0.0:5001
```

### Production Deployment (Vercel)

**Hosting**: Vercel project `oregonizertrail` (team `nathan-ramias-projects`), served at https://oregonizertrail.vercel.app. The GitHub repo is *not* connected to Vercel; deploys go out from the local checkout via the Vercel CLI.

**Database**: Neon Postgres (`oregonizertrail-db`), attached through the Vercel Marketplace, which injects `DATABASE_URL` / `DATABASE_URL_UNPOOLED` into the project env.

**Environment Variables** (Vercel → Settings → Environment Variables, Production):
- `DATABASE_URL`, `DATABASE_URL_UNPOOLED` (from the Neon integration)
- `SECRET_KEY` (required: serverless instances must share one key or sessions break)
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI=https://oregonizertrail.vercel.app/authorize`

The Google OAuth client lives in the `oregonizer-trail` Google Cloud project (nbramia@gmail.com). Its authorized redirect URIs must include the URI above.

**Serverless game state**: Vercel doesn't keep process memory between requests, so each user's in-progress game is serialized (`developmentGame.to_state()`) into the `game_state` table after every request and rebuilt (`from_state()`) on the next one.

**Deployment Process**:
```bash
./deploy.sh "Your commit message describing the changes"

# The script:
# 1. Runs all tests (aborts if any fail)
# 2. Commits and pushes to GitHub
# 3. Pulls production env from Vercel, runs `flask db upgrade` and
#    `populate_scenarios.py` against Neon (Heroku's old release phase)
# 4. Runs `vercel deploy --prod`
```

**Manual**:
```bash
vercel env pull /tmp/prod.env --environment=production --yes
export DATABASE_URL=$(grep '^DATABASE_URL_UNPOOLED=' /tmp/prod.env | cut -d= -f2- | tr -d '"')
flask --app app db upgrade && python populate_scenarios.py
unset DATABASE_URL; rm /tmp/prod.env
vercel deploy --prod
```

**Warning**: never run the test suite with `DATABASE_URL` pointing at production. The tests swap to SQLite only after `app` is imported, so they would write to (and `drop_all` on) the real database.

### Database Connection Logic (app.py:28-36)

```python
database_url = os.environ.get('DATABASE_URL')
if database_url:
    database_url = database_url.replace("postgres://", "postgresql://")
else:
    database_url = 'sqlite:///app.db'

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
```

- Some providers (e.g. Heroku) supply `DATABASE_URL` with a `postgres://` scheme
- SQLAlchemy 2.x requires `postgresql://` scheme
- Automatic replacement for compatibility
- Falls back to SQLite for local development without env var

## Development Workflow

### Utility Scripts

**User Management**:
- `create_user.py`: Create single user interactively
- `create_many_users.py`: Bulk user creation
- `delete_user.py`: Delete user by email
- `clear_users.py`: Delete all users

**Scenario Management**:
- `populate_scenarios.py`: Load scenarios from scenarios.py into database
- `create_scenario.py`: Interactive scenario creation
- `delete_scenario.py`: Delete scenario by name
- `delete_all_scenarios.py`: Clear all scenarios
- `update_scenario_metrics.py`: Modify existing scenario metrics

**Database**:
- `create_db.py`: Initialize database tables (legacy, use Flask-Migrate)
- `manage.py`: Flask-Migrate management script

### Testing Workflow

1. **Test Authentication**:
   - Email/password login
   - Google OAuth login
   - Logout and session clearing

2. **Test Game Flow**:
   - Start game with each difficulty level
   - Play through decision scenarios
   - Verify informational scenarios trigger
   - Test win/loss conditions

3. **Test Scenario Handling**:
   - Verify metric changes apply correctly
   - Check variation ranges affect outcomes
   - Confirm tech debt auto-decay

4. **Test Community Features**:
   - Create custom scenario
   - Toggle community scenarios on/off
   - Rate scenarios and responses

5. **Test Statistics**:
   - Verify games_started increments at Turn 2
   - Confirm games_played increments on end_game
   - Check high_score updates correctly
   - Review leaderboard accuracy

## Environment Configuration

### Required Environment Variables

**DATABASE_URL**:
- Format: `postgresql://user:password@host:port/database`
- Vercel's Neon integration auto-provides this (plus `DATABASE_URL_UNPOOLED`, used for migrations)
- Local: Set in `.env` file

**SECRET_KEY**:
- Flask session secret key
- Generate with: `python -c "import os; print(os.urandom(24).hex())"`
- Must be set for production to persist sessions across deploys
- Fallback: Auto-generates on startup (sessions lost on restart)

**GOOGLE_CLIENT_ID**:
- OAuth 2.0 Client ID from Google Cloud Console
- Required for Google Sign-In functionality
- Get from: https://console.cloud.google.com/

**GOOGLE_CLIENT_SECRET**:
- OAuth 2.0 Client Secret from Google Cloud Console
- Required for Google Sign-In functionality
- Keep confidential - never commit to source control

**GOOGLE_REDIRECT_URI**:
- Local: `http://localhost:5001/authorize`
- Production: `https://www.oregonizertrail.org/authorize`
- Must match Google OAuth Console configuration

### Setting Environment Variables

**Local Development (.env file)**:
```bash
DATABASE_URL=postgresql://localhost/oregonizer_trail
SECRET_KEY=your-secret-key-here
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:5001/authorize
```

**Heroku Production**:
```bash
heroku config:set SECRET_KEY="$(python -c 'import os; print(os.urandom(24).hex())')"
heroku config:set GOOGLE_CLIENT_ID="your-client-id.apps.googleusercontent.com"
heroku config:set GOOGLE_CLIENT_SECRET="your-client-secret"
heroku config:set GOOGLE_REDIRECT_URI="https://www.oregonizertrail.org/authorize"
```

### OAuth Configuration

**Google Cloud Console Setup**:
1. Go to https://console.cloud.google.com/
2. Create or select a project
3. Enable Google+ API
4. Create OAuth 2.0 Client ID (Web application)
5. Add authorized redirect URIs:
   - Local: `http://localhost:5001/authorize`
   - Production: `https://www.oregonizertrail.org/authorize`
6. Copy Client ID and Client Secret
7. Set as environment variables (see above)

**Security Note**: All credentials are now loaded from environment variables. Never commit credentials to source control.

## Gameplay Examples

### Example Decision Scenario

**Scenario**: "A feature is taking longer than anticipated. Push the team to hit the projected timeline?"

**If Yes**:
- Staff Retention: -35 (modified by variation range)
- Message: "Pushed the team to hit the deadline. Staff retention decreased. Partner retention held steady."

**If No**:
- Staff Retention: +25 (modified)
- Partner Growth: -15 (modified)
- Partner Retention: -15 (modified)
- Message: "Allowed delay. Staff retention increased, partner growth and retention slightly decreased."

### Example Informational Scenario

**Scenario**: "Amazon Web Services outage - the platform went down for 24h."

**Automatic Effects**:
- Partner Retention: -25 (modified by variation range)
- No player choice; metrics updated immediately
- Message displayed, player clicks "Next"

### Tech Debt Auto-Decay Example

**Turn Start**:
- Partner Growth: 120
- Partner Retention: 80
- Tech Debt: 100

**Calculation**:
```python
debt_factor = round((120 + 80) / 200)  # = round(1.0) = 1
new_tech_debt = max(0, 100 - 1)  # = 99
```

**Result**: Tech debt decreases by 1 this turn

### Win Scenario Example 1: Survival Victory

**Turn 25 Status**:
- Staff Retention: 45
- Partner Growth: 30
- Partner Retention: 60
- Tech Debt: 20

**Result**: "Congratulations! You've survived 25 turns and avoided any major issues."

### Win Scenario Example 2: Thriving Victory

**Turn 12 Status**:
- Staff Retention: 110
- Partner Growth: 105
- Partner Retention: 115
- Tech Debt: 40

**Result**: "Congratulations! Well into the game, all key metrics are above 100. You're thriving!"

## Scoring System

### Score Calculation (routes/game.py:153-189)

**Difficulty Score**:
- Normal: 50 points
- Hard: 75 points
- Crazy: 100 points

**Survival Score**:
- Won (reached Turn 25 or thriving): 100 points
- Lost: `min(4 * turns_survived, 100)`

**Points Score**:
- Average of all non-tech_debt metrics (capped at 0-100 each)
- Varies by mode (number of metrics differs)

**Overall Score** (Weighted):
```python
# Difficulty and Survival are double-weighted (40% each)
# Points are single-weighted (20%)
overall_score = (2 * difficulty_score + 2 * survival_score + points_score) / 5
```

This weighted formula emphasizes strategic difficulty selection and longevity over just maintaining high metrics.

### Maximum Possible Score

**Perfect Score = 100**:
- Difficulty: Crazy (100)
- Survival: Win (100)
- Points: All metrics at 100 (100)
- Overall: (2×100 + 2×100 + 100) / 5 = 100

**Realistic High Score**:
- Difficulty: Crazy (100)
- Survival: 25 turns (100)
- Points: Metrics averaging ~80 (~80)
- Overall: (2×100 + 2×100 + 80) / 5 = 96

## Game Constraints

### Scenario Constraints
- Decision scenarios: Metrics between -30 and 30 for each choice
- Informational scenarios: Metrics between -30 and 30
- Scenario names: Lowercase alphanumeric with underscores only
- Scenario text: Required, no length limit
- Response text: Required for decision scenarios

### Gameplay Constraints
- Minimum turns: 0 (can lose immediately on Turn 1)
- Maximum tracked turns: 25 (auto-win)
- Metrics: Capped at 0-100 during gameplay (automatically clamped)
- Community scenarios: Must manually toggle to enable
- Scenario queues: Auto-refresh when exhausted (no scenario limit)

### Technical Constraints
- **Multi-user Support**: ✅ Per-user game instances support concurrent gameplay
- Session-based authentication: Server-side sessions required
- Database: Requires PostgreSQL or SQLite
- Frontend: No mobile app; web-only interface
- CSRF Protection: All POST/PUT/DELETE requests require valid CSRF token

## Code Patterns and Standards

### Backend Patterns

**Route Organization** (Flask Blueprints in routes/):
- **Authentication** (routes/auth.py): `/`, `/login`, `/logout`
- **OAuth** (routes/oauth.py): `/login/google`, `/authorize`
- **Game** (routes/game.py): `/reset_game`, `/next_turn`, `/handle_scenario`, `/end_game`
- **Settings** (routes/settings.py): `/set_difficulty`, `/set_mode`, `/set_include_community_scenarios`
- **Data** (routes/data.py): `/get_user_info`, `/get_leaderboard`, `/get_modes`, `/get_mode_metrics`
- **Scenarios** (routes/scenarios.py): `/create_scenario`, `/rate_scenario`, `/get_ratings`

**Error Handling**:
- Try-except blocks on all routes
- Logging with `logging.debug()`, `logging.error()`, `logging.warning()`
- JSON error responses with appropriate HTTP status codes
- Input validation with descriptive 400 errors
- CSRF validation on all state-changing requests

**Database Patterns**:
- SQLAlchemy ORM for all queries
- Explicit `db.session.commit()` after mutations
- JSON deserialization with `json.loads()` for metrics/responses
- Filters by mode, type, and community flag on scenario queries

### Frontend Patterns

**State Management** (index.html JavaScript):
- Global `gameState` variable for game phase
- DOM manipulation for UI updates
- Fetch API for all backend communication
- Modal-based UI for settings, overlays, score details

**UI Update Pattern**:
```javascript
fetch('/endpoint', { method: 'POST', body: data })
  .then(response => response.json())
  .then(data => {
    updateMetrics(data.metrics);
    displayScenario(data);
  })
  .catch(error => console.error(error));
```

**Metric Display**:
- Health bar visualization (CSS width based on percentage)
- Turn counter display
- Color-coded status (green: #0dd635)

### Responsive Design

**Breakpoints**:
- Mobile: < 496px (hide rating buttons, compact metrics)
- Tablet: 496px - 768px (adjusted layout)
- Desktop: > 768px (full layout)

**Mobile Optimizations**:
- Stacked metric bars with reduced size
- Hidden rating buttons (space constraints)
- Bottom-aligned mode/difficulty display
- Responsive button positioning

## Troubleshooting

### Common Issues

**Database Connection Errors**:
- Verify `DATABASE_URL` in `.env`
- Check PostgreSQL service running locally
- Confirm Heroku Postgres add-on provisioned

**OAuth Redirect Mismatch**:
- Ensure `GOOGLE_REDIRECT_URI` matches Google Console
- Verify redirect URI in OAuth client configuration
- Check HTTP vs HTTPS protocol match

**Session Issues**:
- Clear browser cookies
- Verify `app.secret_key` is set (app.py:26)
- Check Flask session configuration

**Scenario Not Loading**:
- Verify scenarios exist in database: `Scenario.query.all()`
- Check mode filter matches selected mode
- Confirm community scenario toggle state
- Run `populate_scenarios.py` to load default scenarios

**Metrics Not Updating**:
- Check browser console for JavaScript errors
- Verify `/handle_scenario` endpoint returning metrics
- Confirm `updateMetrics()` function executing

**High Score Not Saving**:
- Verify user authenticated (check `current_user.is_authenticated`)
- Confirm `/end_game` endpoint called with correct data
- Check database commit successful (no SQLAlchemy errors)

### Debug Mode

**Enable Flask Debug Logging** (app.py:20):
```python
logging.basicConfig(level=logging.DEBUG)
```

**Run Flask Debug Server** (app.py:533-534):
```python
app.run(debug=True, host='0.0.0.0', port=5001)
```

### Database Inspection

**Check User Data**:
```python
from app import app, db, User
with app.app_context():
    users = User.query.all()
    for user in users:
        print(f"{user.email}: {user.high_score} points, {user.games_played} games")
```

**Check Scenario Count**:
```python
from app import app, db, Scenario
with app.app_context():
    print(f"Decision: {Scenario.query.filter_by(type='decision').count()}")
    print(f"Informational: {Scenario.query.filter_by(type='informational').count()}")
    print(f"Community: {Scenario.query.filter_by(community=True).count()}")
```

---

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Setting up a local development environment
- Submitting bug reports and feature requests
- Creating pull requests
- Adding new game scenarios

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

---

## Quick Start Summary

**For Local Development**:
```bash
# 1. Setup
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Configure
echo "DATABASE_URL=sqlite:///app.db" > .env
echo "GOOGLE_REDIRECT_URI=http://localhost:5001/authorize" >> .env

# 3. Database
flask db upgrade
python populate_scenarios.py

# 4. Run
python app.py
# Navigate to http://localhost:5001
```

**For Heroku Deployment**:
```bash
# 1. Create app
heroku create oregonizer-trail

# 2. Add Postgres
heroku addons:create heroku-postgresql

# 3. Configure
heroku config:set GOOGLE_REDIRECT_URI=https://oregonizer-trail.herokuapp.com/authorize

# 4. Deploy
git push heroku master

# 5. Migrate and seed
heroku run flask db upgrade
heroku run python populate_scenarios.py
```
