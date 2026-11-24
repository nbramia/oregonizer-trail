# Contributing to Oregonizer Trail

Thank you for your interest in contributing to Oregonizer Trail!

## Getting Started

### Prerequisites

- Python 3.12
- PostgreSQL is optional; local development uses SQLite by default

### Local Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/nbramia/oregonizer-trail.git
   cd oregonizer-trail
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```
   The app and the migrations read the database from `DATABASE_URL`. If it is unset, the app uses SQLite at `sqlite:///app.db`. Google sign-in needs `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `GOOGLE_REDIRECT_URI`; see the Configuration section of the [README](README.md).

4. Create the schema and load scenarios:
   ```bash
   flask db upgrade
   python populate_scenarios.py
   ```

5. Run the application:
   ```bash
   python app.py
   ```

   The app will be available at http://localhost:5001

### Running Tests

```bash
env -u DATABASE_URL python3 -m unittest discover -s . -p "test_*.py"
```

Never run the tests with `DATABASE_URL` pointing at a real database.

## How to Contribute

### Reporting Bugs

- Open an issue describing the bug
- Include steps to reproduce
- Include expected vs actual behavior

### Suggesting Features

- Open an issue with the "enhancement" label
- Describe the feature and its use case

### Submitting Code

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes
4. Test your changes locally
5. Commit with clear messages
6. Push to your fork
7. Open a Pull Request

### Code Style

- Follow PEP 8 for Python code
- Keep functions focused and small
- Add comments for complex logic

## Creating Scenarios

Game scenarios are a great way to contribute. Scenarios can be:

- **Decision scenarios**: present a choice with "Yes" or "No" options, each affecting metrics differently
- **Informational scenarios**: share information that affects metrics without requiring a choice

Scenarios are defined in the `scenarios_*.csv` files (one per mode), which `populate_scenarios.py` loads into the database. Use an existing row as a template for the columns. Each mode has its own metrics (see `mode_config.py`); for Movement Labs they are `staff_retention`, `revenue`, `net_votes`, and `tech_debt`.

## License

By contributing, you agree that your contributions will be licensed under the GPL v3 License.
