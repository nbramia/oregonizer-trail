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

A web-based simulation game where players manage critical metrics through decision-making scenarios while navigating external events, all in a retro terminal-style interface. Live at https://oregonizertrail.vercel.app.

## Table of Contents

- [Core Features](#core-features)
- [Game Rules and Behavior](#game-rules-and-behavior)
- [Gameplay Examples](#gameplay-examples)
- [Scoring System](#scoring-system)
- [Tech Stack](#tech-stack)
- [Architecture and Code Organization](#architecture-and-code-organization)
- [Database Schema](#database-schema)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Testing](#testing)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Core Features

### Game Modes

Each mode has its own scenarios and metrics. Modes are configured in `mode_config.py`.

| Mode | Status | Metrics |
|------|--------|---------|
| Movement Labs | Enabled (default) | Staff Retention, Revenue, Net Votes, Tech Debt |
| Product Development | Defined, disabled | Staff Retention, Partner Retention, Partner Growth, Tech Debt |
| Partnership & Support | Defined, disabled | Staff Retention, Partner Retention, Partner Growth, Tech Debt |

To enable or disable a mode, edit its entry in `MODES` in `mode_config.py`:

```python
{
    'name': 'Product Development',
    'enabled': False,   # True to show this mode
    'default': False,   # Exactly one enabled mode should be the default
    'description': '...',
    'metrics': ['staff_retention', 'partner_retention', 'partner_growth', 'tech_debt']
}
```

Scenarios for every mode, including disabled ones, live in `scenarios_*.csv`. Changes to `mode_config.py` take effect on the next deploy.

### Scenario Types

1. **Decision scenarios**: a Yes/No choice that affects metrics differently depending on the answer.
2. **Informational scenarios**: external events that happen regardless of choice, reflecting real-world unpredictability. They are never shown on turn 1 or twice in a row, and otherwise appear with a 20% chance each turn.

### Difficulty Levels

| Level | Starting metrics | Starting tech debt | Variation range |
|-------|------------------|--------------------|-----------------|
| Normal | 100 | 100 | 0.8-1.25x |
| Hard | 85 | 75 | 1.0-1.4x |
| Crazy | 75 | 50 | 1.1-1.6x |

### Community Features

- **Scenario creation**: signed-in users can submit custom scenarios, which are validated before they are saved.
- **Toggle control**: players can include or exclude community-submitted scenarios (excluded by default).

### Authentication

- **Google OAuth**: single sign-on; an account is created on first sign-in.
- **Email/password**: login for existing accounts with a bcrypt-hashed password.

### User Statistics

- **High Score**: best overall score (see [Scoring System](#scoring-system))
- **Games Started**: games that reached turn 2
- **Games Played**: games that reached an end state (win or loss)
- **Last Played**: timestamp of the most recent completed game
- **Leaderboard**: top 10 high scores

## Game Rules and Behavior

### Core Metrics

All metrics range from 0 to 100 and are clamped to that range. The game ends in failure when any metric reaches 0 or below.

**Movement Labs mode**

1. **Staff Retention**: team morale, burnout, and retention
2. **Revenue**: organizational financial sustainability
3. **Net Votes**: progress toward the mission and impact goals
4. **Tech Debt**: platform stability and technical health. Each turn it decreases by `round((revenue + net_votes) / 200)`.

**Product Development and Partnership & Support modes**

1. **Staff Retention**
2. **Partner Retention**: existing customer satisfaction and renewals
3. **Partner Growth**: new customer acquisition and market expansion
4. **Tech Debt**: each turn it decreases by `round((partner_growth + partner_retention) / 200)`.

Higher scores on the other metrics therefore erode tech debt faster.

### Turn Progression

1. The turn counter increments.
2. Tech debt is adjusted.
3. A scenario is selected. An informational scenario is shown with 20% probability (never on turn 1, never twice in a row); otherwise a decision scenario is shown. Each type is drawn from its own shuffled queue, which is reshuffled when exhausted.
4. Informational scenarios apply their effects immediately; decision scenarios wait for the player's Yes/No answer.
5. Win and loss conditions are checked.

### Metric Variation

Every metric change is scaled by a random factor drawn from the difficulty's variation range:

```python
actual_change = int(base_change * random.uniform(*variation_range))
```

The same decision can therefore have different magnitudes of effect.

### Win Conditions

Players win by achieving **either**:

1. **Survival Victory**: reach turn 25 with no metric at or below 0.
2. **Thriving Victory**: from turn 10 onward, every non-tech-debt metric at 100.

### Loss Conditions

The game ends immediately when any metric drops to 0 or below, with a message specific to that metric. If several metrics fail at once, all messages are shown. Failures take priority over wins.

### Scenario Selection

- Scenarios are loaded from the database, filtered by the selected mode and the community toggle.
- Queues are shuffled at game start and refilled when empty, preventing immediate repetition.

## Gameplay Examples

### Decision Scenario

**Scenario**: "A feature is taking longer than anticipated. Push the team to hit the projected timeline?" (Product Development mode)

**If Yes**:
- Staff Retention: -35 (scaled by the variation range)

**If No**:
- Staff Retention: +25
- Partner Growth: -15
- Partner Retention: -15

### Informational Scenario

**Scenario**: "Amazon Web Services outage - the platform went down for 24h."

- Partner Retention: -25 (scaled by the variation range)
- No player choice; metrics update immediately and the player clicks "Next".

### Tech Debt Decay (Product Development mode)

With Partner Growth 100, Partner Retention 80, and Tech Debt 100:

```python
debt_factor = round((100 + 80) / 200)   # round(0.9) = 1
new_tech_debt = max(0, 100 - 1)         # 99
```

### Survival Victory

On turn 25 with Staff Retention 45, Partner Growth 30, Partner Retention 60, Tech Debt 20, the player wins: "You've survived 25 turns and avoided any major issues."

### Thriving Victory

On turn 12 with Staff Retention, Partner Growth, and Partner Retention all at 100 (Tech Debt 40), the player wins: "Well into the game, all key metrics are at 100. You're thriving!"

## Scoring System

Scores are calculated in `routes/game.py` when a game ends.

| Component | Value |
|-----------|-------|
| Difficulty score | Normal 50, Hard 75, Crazy 100 |
| Turns score | `min(turns_survived / 25 * 100, 100)` |
| Win bonus | 100 if the game was won, otherwise 0 |
| Points score | Average of the final metrics other than tech debt, each clamped to 0-100 |

```python
overall_score = (2 * difficulty_score + turns_score + win_bonus + points_score) / 5
```

Difficulty carries a 40% weight; turns, win bonus, and points carry 20% each. A won 25-turn game on Crazy with every non-tech-debt metric at 100 scores 100. Tech debt ends the game at zero but doesn't count toward points.

## Tech Stack

- **Backend**: Python 3.12, Flask 3.0.3, Flask-SQLAlchemy 3.1.1 with SQLAlchemy 2.0.x (pinned `<2.1`), Flask-Migrate (Alembic), Flask-Login 0.6.3, Flask-WTF 1.2.1 (CSRF), bcrypt 3.2.0, Authlib (Google OAuth), python-dotenv 0.19.2, gunicorn 22.0.0
- **Frontend**: vanilla JavaScript single-page app, Tailwind CSS 2.2.19 (CDN), Press Start 2P font (Google Fonts), Font Awesome 6 (CDN), Tenor embeds for animated GIFs
- **Database**: PostgreSQL in production (Neon, via the Vercel Marketplace) with psycopg2-binary 2.9.9; SQLite locally by default
- **Hosting**: Vercel (serverless Python, Flask framework preset in `vercel.json`)

Exact dependency pins are in `requirements.txt`.

## Architecture and Code Organization

### File Structure

```
.
├── app.py                      # Flask app: config, extensions, OAuth, game persistence, blueprint registration
├── game_logic.py               # Game engine (developmentGame class)
├── models.py                   # SQLAlchemy models (User, Scenario, GameState)
├── config.py                   # Config class (database URI, secret key)
├── mode_config.py              # Game modes and their metrics
├── validation.py               # Input validation for API endpoints
├── populate_scenarios.py       # Loads scenarios_*.csv into the database
├── scenarios_*.csv             # Scenario data, one file per mode
├── scenarios.py, utilities.py  # Helper modules not imported by the app
├── routes/
│   ├── auth.py                 # Email/password login, logout, auth check
│   ├── oauth.py                # Google OAuth
│   ├── game.py                 # reset, next turn, handle scenario, end game and scoring
│   ├── settings.py             # Difficulty, mode, community toggle
│   ├── data.py                 # User info, leaderboard, modes, mode metrics
│   └── scenarios.py            # Community scenario creation
├── migrations/                 # Alembic migrations
├── templates/index.html        # Single-page frontend
├── static/                     # game.js, CSS, icons, terms and privacy text
├── test_*.py                   # unittest suite
├── deploy.sh                   # Test, push, migrate, and deploy script
├── vercel.json                 # Vercel config
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable template
├── CONTRIBUTING.md
└── LICENSE
```

### Game State Persistence

Serverless instances do not share memory, so each player's in-progress game is stored in the `game_state` table, keyed `user_<id>` (or `temp_<session id>` for unauthenticated sessions):

- `get_game()` in `app.py` rebuilds the game with `developmentGame.from_state()` once per request and caches it on `flask.g`.
- An `after_request` hook saves `to_state()` back to the database.
- Scenarios are serialized as IDs. Any new game attribute must be added to both `to_state()` and `from_state()` in `game_logic.py`.
- Logging out deletes the user's saved game.

### Scenario Storage

Scenarios live in the `scenario` table, not in code. `populate_scenarios.py` loads every `scenarios_*.csv` file, replacing all non-community scenarios and leaving community scenarios untouched. It parses every file before touching the database and exits non-zero if anything fails, so a bad CSV can't empty a mode or let `deploy.sh` continue. Metrics and responses are stored as JSON strings and decoded at runtime.

Decision scenario metrics:

```json
{
  "yes": {"staff_retention": -35, "partner_growth": 0, "partner_retention": -15, "tech_debt": 20},
  "no":  {"staff_retention": 25, "partner_growth": -15, "partner_retention": -10, "tech_debt": 0}
}
```

Informational scenario metrics:

```json
{"staff_retention": -20, "partner_growth": 10, "partner_retention": -5, "tech_debt": 15}
```

Decision scenarios also carry a `response` JSON object with `yes` and `no` message strings.

### Validation and Security

- CSRF protection (Flask-WTF) on all POST/PUT/DELETE requests; the frontend's `fetchWithCSRF()` adds the `X-CSRFToken` header.
- `validation.py` checks request input and returns 400 with a descriptive message on failure:
  - `/set_difficulty` and `/end_game`: difficulty must be `Normal`, `Hard`, or `Crazy`; `turns_survived` an integer from 0 to 1000; metric values 0-200.
  - `/create_scenario`: name (up to 200 characters), mode (must be enabled), type (`decision` or `informational`), text (up to 5000 characters), metrics JSON (only the mode's metrics, each value between -100 and 100), and a `yes`/`no` response JSON for decision scenarios.
- Passwords are hashed with bcrypt.
- Secrets come from environment variables.

### Authentication Flow

- **Email/password**: credentials are POSTed to `/` or `/login`, checked with bcrypt, and a Flask-Login session is created.
- **Google OAuth**: `/login/google` starts the flow, Google redirects to `/authorize`, and `User.get_or_create()` creates the account on first sign-in.

### Routes

| Blueprint | Routes |
|-----------|--------|
| `routes/auth.py` | `/`, `/login`, `/logout`, `/check_auth` |
| `routes/oauth.py` | `/login/google`, `/authorize` |
| `routes/game.py` | `/reset_game`, `/next_turn`, `/handle_scenario`, `/end_game` |
| `routes/settings.py` | `/set_difficulty`, `/set_mode`, `/set_include_community_scenarios` |
| `routes/data.py` | `/get_user_info`, `/get_leaderboard`, `/get_modes`, `/get_mode_metrics` |
| `routes/scenarios.py` | `/create_scenario` |

## Database Schema

### user

| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | Primary key |
| email | String(128) | Unique, not null |
| password | String(128) | Nullable |
| high_score | Integer | Default 0 |
| games_played | Integer | Default 0 |
| games_started | Integer | Default 0 |
| last_game_played | DateTime | Default none |

### scenario

| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | Primary key |
| name | String(128) | Unique, not null |
| mode | String(128) | Not null |
| type | String(128) | Not null (`decision` or `informational`) |
| text | Text | Not null |
| metrics | Text | Not null (JSON string) |
| response | Text | Nullable (JSON string, decision scenarios only) |
| community | Boolean | Default false |

### game_state

| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | Primary key |
| user_key | String(128) | Unique, not null |
| state | Text | Not null (JSON from `developmentGame.to_state()`) |
| updated_at | DateTime | Default now, updated on change |

Schema changes go through Alembic: `flask db migrate -m "description"` then `flask db upgrade`.

## Getting Started

Prerequisites: Python 3.12 and git. PostgreSQL is optional; local development uses SQLite by default.

```bash
# 1. Clone and install
git clone https://github.com/nbramia/oregonizer-trail.git
cd oregonizer-trail
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure (see Configuration below)
cp .env.example .env
# edit .env: set Google OAuth credentials if you want Google sign-in

# 3. Create the schema and load scenarios
flask db upgrade
python populate_scenarios.py

# 4. Run
python app.py                    # http://localhost:5001
```

`python app.py` listens on port 5001 unless `PORT` is set. Accounts are created on first Google sign-in, so Google OAuth credentials are needed to sign in locally.

## Configuration

The app reads these environment variables. Locally, put them in a `.env` file at the repo root (gitignored; `.env.example` is the template). In production they are set in the Vercel project.

| Variable | Required | Purpose |
|----------|----------|---------|
| `DATABASE_URL` | No | Database connection string. `app.py` reads it after `load_dotenv()`; if unset, the app uses SQLite at `sqlite:///app.db`. A `postgres://` scheme is rewritten to `postgresql://`. |
| `SECRET_KEY` | Production | Flask session key. If unset, a random key is generated per process, which breaks sessions across serverless instances. Generate one with `python3 -c "import os; print(os.urandom(24).hex())"`. |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | For Google sign-in | OAuth 2.0 client credentials. |
| `GOOGLE_REDIRECT_URI` | For Google sign-in | OAuth callback. Locally `http://localhost:5001/authorize`; in production `https://oregonizertrail.vercel.app/authorize`. Must match an authorized redirect URI on the OAuth client. |
| `BASE_DOMAIN` | No | If set, requests whose host equals it are redirected (301) to `https://www.<BASE_DOMAIN>`. |

### Database

The app and the migrations both take the database from `DATABASE_URL`. `migrations/env.py` reads the URL from the Flask app's engine, so `alembic.ini` holds no URL. In production, Vercel's Neon integration provides `DATABASE_URL` (pooled) and `DATABASE_URL_UNPOOLED`; `deploy.sh` runs migrations with `DATABASE_URL_UNPOOLED`.

### Google OAuth Setup

1. In the [Google Cloud Console](https://console.cloud.google.com/), create or select a project.
2. Configure the OAuth consent screen.
3. Under Credentials, create an OAuth client ID of type Web application.
4. Add authorized redirect URIs: `http://localhost:5001/authorize` and your production `/authorize` URL.
5. Put the client ID and secret in `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`.

Never commit credentials; `.env` is gitignored.

## Testing

```bash
python3 -m unittest discover -s . -p "test_*.py"
```

Tests use an in-memory SQLite database. **Never run the tests with `DATABASE_URL` pointing at production**: the tests switch to SQLite only after `app` is imported, so they would write to the real database. Run them with `DATABASE_URL` unset (for example `env -u DATABASE_URL python3 -m unittest discover -s . -p "test_*.py"`).

What the suite covers:

| File | Covers |
|------|--------|
| `test_game_logic.py` | The game engine: difficulty, tech-debt decay, scenario selection, metric changes, win/loss checks, in Product Development mode and in the default Movement Labs mode |
| `test_game_end_scenarios.py` | Every combination of metrics hitting zero, and failure taking priority over wins |
| `test_game_state.py` | Saving and restoring a game between requests, including after scenarios are reloaded |
| `test_routes.py` | The HTTP endpoints: login, turns, choices, scoring, settings, scenario creation |
| `test_models.py` | The `user` and `scenario` models |
| `test_validation.py` | Input validators |
| `test_scenario_data.py` | Every row in `scenarios_*.csv` parses and validates for its mode |

Manual checks worth running after changes: sign in with Google, play each difficulty, confirm informational scenarios and win/loss messages, create a community scenario and toggle community scenarios, and confirm `games_started`, `games_played`, high score, and the leaderboard update.

## Deployment

Production runs on Vercel at https://oregonizertrail.vercel.app, with a Neon Postgres database attached through the Vercel Marketplace. The GitHub repo is not connected to Vercel; deploys go out from a local checkout with the Vercel CLI.

**Vercel environment variables** (Production): `DATABASE_URL`, `DATABASE_URL_UNPOOLED` (from the Neon integration), `SECRET_KEY`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `GOOGLE_REDIRECT_URI=https://oregonizertrail.vercel.app/authorize`.

**Deploy**:

```bash
./deploy.sh "Commit message"
```

`deploy.sh`:

1. Runs the test suite and aborts if it fails.
2. Commits all changes and pushes to `main` on GitHub.
3. Pulls the production environment with `vercel env pull`, then runs `flask db upgrade` and `populate_scenarios.py` against `DATABASE_URL_UNPOOLED`.
4. Runs `vercel deploy --prod`.

**Manual**:

```bash
vercel env pull /tmp/prod.env --environment=production --yes
export DATABASE_URL=$(grep '^DATABASE_URL_UNPOOLED=' /tmp/prod.env | cut -d= -f2- | tr -d '"')
flask --app app db upgrade && python populate_scenarios.py
unset DATABASE_URL; rm /tmp/prod.env
vercel deploy --prod
```

## Troubleshooting

**Database connection errors**: check `DATABASE_URL` in `.env`, or unset it to use SQLite. For a local PostgreSQL URL, confirm the server is running.

**Missing tables**: run `flask db upgrade`.

**No scenarios appear**: run `python populate_scenarios.py`; confirm scenarios exist for the selected mode and that the community toggle matches what you expect.

**OAuth redirect mismatch**: `GOOGLE_REDIRECT_URI` must exactly match an authorized redirect URI on the OAuth client, including `http` vs `https`.

**Sessions reset unexpectedly**: set `SECRET_KEY`. Without it, each process generates its own key.

**High score not saving**: the user must be signed in, and `/end_game` must succeed (check server logs for validation or database errors).

**Metrics not updating**: check the browser console and the response from `/handle_scenario`.

Debug logging is enabled by default (`logging.basicConfig(level=logging.DEBUG)` in `app.py`).

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, issue and pull request guidelines, and how to add scenarios.

## License

This project is licensed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for details.
