# Contributing to Oregonizer Trail

Thank you for your interest in contributing to Oregonizer Trail!

## Getting Started

### Prerequisites

- Python 3.12+
- PostgreSQL (or SQLite for local development)

### Local Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/nbramia/oregonizer-trail.git
   cd oregonizer-trail
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Initialize the database:
   ```bash
   python create_db.py
   flask db upgrade
   python populate_scenarios.py
   ```

6. Run the application:
   ```bash
   python app.py
   ```

   The app will be available at http://localhost:5001

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

Game scenarios are a great way to contribute! Scenarios can be:

- **Decision scenarios**: Present a choice with "Yes" or "No" options, each affecting metrics differently
- **Informational scenarios**: Share information that affects metrics without requiring a choice

See existing scenarios in the database for examples of the format.

## License

By contributing, you agree that your contributions will be licensed under the GPL v3 License.
