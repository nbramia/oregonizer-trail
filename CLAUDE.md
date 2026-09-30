# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

"Oregonizer Trail" is a Flask-based web game simulating organizational/product development challenges. Players manage four key metrics (staff retention, partner retention, partner growth, tech debt) through decision-making scenarios across multiple game modes.

## Core Architecture

### Application Structure
- **app.py**: Main Flask application with routes, OAuth setup, and application initialization
- **game_logic.py**: Core game engine (`developmentGame` class) managing game state, scenario selection, metric updates, and turn progression
- **models.py**: SQLAlchemy models for User, Scenario, and Rating
- **scenarios.py**: Legacy scenario definitions (older class-based format, largely superseded by database storage)
- **config.py**: Configuration class for database URI and secret key

### Database Models
- **User**: Authentication (email/password or Google OAuth), game statistics (high_score, games_played, games_started)
- **Scenario**: Game scenarios with name, mode, type (decision/informational), text, metrics (JSON), response (JSON), and community flag
- **Rating**: User ratings (thumbs up/down) for scenarios and responses

### Game Logic Flow
1. Game initialization sets difficulty-based starting values
2. `next_turn()` increments turn counter, adjusts tech debt, selects scenario (75% decision, 25% informational)
3. Scenario queues are shuffled and cycled to avoid repetition
4. Metric changes are applied with difficulty-based variation ranges
5. Status checks determine win/loss conditions

### Key Design Patterns
- Scenarios stored in database, loaded and queued at game start
- Metrics stored as JSON strings in database, deserialized at runtime
- Variation ranges scale with difficulty (Normal: 0.8-1.25, Hard: 1.0-1.4, Crazy: 1.1-1.6)
- Tech debt automatically decreases each turn based on partner metrics
- Community scenarios can be toggled on/off, filtered at query time

## Development Commands

### Running the Application
```bash
# Local development
python app.py  # Runs on http://0.0.0.0:5001

# Using gunicorn (production)
gunicorn app:app
```

### Database Management
```bash
# Initialize database
python create_db.py

# Run migrations
flask db upgrade

# Create new migration
flask db migrate -m "description"
```

### User Management Utilities
```bash
python create_user.py      # Create single user
python create_many_users.py # Bulk user creation
python delete_user.py       # Delete user by email
python clear_users.py       # Clear all users
```

### Scenario Management Utilities
```bash
python populate_scenarios.py      # Populate scenarios from scenarios.py
python create_scenario.py         # Interactive scenario creation
python delete_scenario.py         # Delete scenario by name
python delete_all_scenarios.py    # Clear all scenarios
python update_scenario_metrics.py # Update existing scenario metrics
```

## Critical Implementation Details

### Authentication System
- Supports both traditional email/password and Google OAuth
- OAuth redirect URI dynamically set via `GOOGLE_REDIRECT_URI` environment variable
- Flask-Login manages session state
- Passwords hashed with bcrypt

### Environment Variables
Required in `.env`:
- `DATABASE_URL`: PostgreSQL connection string (auto-converts postgres:// to postgresql://)
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`: OAuth client credentials
- `GOOGLE_REDIRECT_URI`: OAuth callback URL (defaults to localhost:5001 for development)
- `SECRET_KEY`: required in production (random per-process fallback breaks sessions on serverless)

### Database Connection
Falls back to SQLite (`sqlite:///app.db`) if `DATABASE_URL` not set. Production uses Neon Postgres (via Vercel Marketplace). SQLAlchemy is pinned `<2.1` because 2.1 defaults `postgresql://` to the psycopg3 driver, and the app ships psycopg2.

### Frontend Architecture
Single-page application in `templates/index.html` with inline JavaScript. Communicates with backend via fetch API for game state, authentication, and scenario handling.

### Scenario Data Structure
Decision scenarios:
```json
{
  "yes": {"staff_retention": -35, "partner_growth": 0, ...},
  "no": {"staff_retention": 25, "partner_growth": -15, ...}
}
```

Informational scenarios:
```json
{"staff_retention": -20, "partner_growth": 10, ...}
```

### Game State Management
Each user's game is stored in the `game_state` table (keyed `user_<id>`), because Vercel's serverless instances don't share memory. `get_game()` in app.py rebuilds it via `developmentGame.from_state()` once per request (cached in `flask.g`); an `after_request` hook saves `to_state()` back. Scenarios are serialized as IDs. Any new game attribute must be added to both `to_state()` and `from_state()`.

## Testing and Deployment

### Local Testing
1. Ensure `.env` exists with `DATABASE_URL` and `GOOGLE_REDIRECT_URI`
2. Run `python app.py`
3. Navigate to `http://localhost:5001`
4. Test authentication, game flow, scenario handling

### Deployment Notes
- Hosted on Vercel: project `oregonizertrail`, live at https://oregonizertrail.vercel.app (Heroku app and oregonizertrail.org are gone)
- `vercel.json` sets the Flask preset; `.python-version` pins 3.12 (force-added, since .gitignore ignores it)
- Deploy with `./deploy.sh "msg"`, which migrates and reseeds Neon (Heroku's old release phase) and then runs `vercel deploy --prod`. GitHub isn't connected to Vercel.
- Env vars live in Vercel: DATABASE_URL(_UNPOOLED), SECRET_KEY, GOOGLE_CLIENT_ID/SECRET, GOOGLE_REDIRECT_URI
- Google OAuth client: GCP project `oregonizer-trail` (nbramia@gmail.com). Redirect URI must match the deployed domain.
- NEVER run tests with DATABASE_URL set to production: tests switch to SQLite only after import and would hit the real DB
- 40 of 83 tests fail on main because they assume the old "Product Development" default mode (only "Movement Labs" is enabled), so deploy.sh's test gate currently blocks

## Working with Nathan's Preferences

Nathan prioritizes **functionality over aesthetics**. When implementing changes:
- Test immediately after each change
- Show ALL code changes across ALL affected files in one response
- Provide clear deployment/testing steps with exact commands
- Focus on reliable solutions over complex/elegant ones
- Update documentation when functionality changes

### Never
- Show partial changes and tell Nathan to make similar changes elsewhere
- Make assumptions without testing
- Skip documentation updates after functional changes
