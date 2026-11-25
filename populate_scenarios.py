import json
import csv
import glob
import os
import sys
from flask import Flask
from models import db, Scenario
from config import Config

SCENARIO_DIR = os.path.dirname(os.path.abspath(__file__))


def load_scenarios_from_csv(csv_path):
    """Load scenarios from a single CSV file and convert to database format"""
    scenarios = []

    with open(csv_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            scenario_data = {
                'name': row['name'],
                'mode': row['mode'],
                'type': row['type'],
                'text': row['text'],
            }

            # Handle decision scenarios
            if row['type'] == 'decision':
                metrics = {
                    'yes': {},
                    'no': {}
                }
                response = {
                    'yes': row['yes_response'],
                    'no': row['no_response']
                }

                # Add yes metrics - support all possible metric types
                metric_types = ['staff_retention', 'partner_retention', 'partner_growth', 'tech_debt', 'revenue', 'net_votes']
                for metric in metric_types:
                    yes_key = f'yes_{metric}'
                    no_key = f'no_{metric}'

                    if row.get(yes_key):
                        metrics['yes'][metric] = int(row[yes_key])
                    if row.get(no_key):
                        metrics['no'][metric] = int(row[no_key])

                scenario_data['metrics'] = json.dumps(metrics)
                scenario_data['response'] = json.dumps(response)

            # Handle informational scenarios
            else:  # type == 'informational'
                metrics = {}

                # Support all possible metric types
                metric_types = ['staff_retention', 'partner_retention', 'partner_growth', 'tech_debt', 'revenue', 'net_votes']
                for metric in metric_types:
                    info_key = f'info_{metric}'
                    if row.get(info_key):
                        metrics[metric] = int(row[info_key])

                scenario_data['metrics'] = json.dumps(metrics)
                scenario_data['response'] = None

            scenarios.append(scenario_data)

    return scenarios


def load_all_mode_scenarios():
    """Load scenarios from every scenarios_*.csv file; a file that fails to parse raises"""
    all_scenarios = []

    csv_files = sorted(glob.glob(os.path.join(SCENARIO_DIR, 'scenarios_*.csv')))

    if not csv_files:
        print("Warning: No scenario CSV files found matching pattern 'scenarios_*.csv'")
        return all_scenarios

    print(f"Found {len(csv_files)} mode-specific CSV file(s):")
    for csv_file in csv_files:
        print(f"  - {os.path.basename(csv_file)}")
        scenarios = load_scenarios_from_csv(csv_file)
        all_scenarios.extend(scenarios)
        print(f"    Loaded {len(scenarios)} scenarios")

    return all_scenarios


def main():
    """Replace the non-community scenarios in DATABASE_URL with the CSV contents"""
    from dotenv import load_dotenv
    load_dotenv()

    app = Flask(__name__)
    app.config.from_object(Config)
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url.replace("postgres://", "postgresql://")
    db.init_app(app)

    # Parse every file before touching the database
    scenarios = load_all_mode_scenarios()
    if not scenarios:
        print("No scenarios loaded; leaving the database unchanged.")
        return 1

    with app.app_context():
        try:
            # Clear only non-community scenarios (preserve user-submitted scenarios)
            print("\nClearing existing CSV scenarios from database...")
            deleted_count = Scenario.query.filter_by(community=False).delete()
            print(f"Deleted {deleted_count} existing CSV scenarios")

            print(f"\nAdding {len(scenarios)} scenarios from CSV files...")
            for scenario_data in scenarios:
                db.session.add(Scenario(
                    name=scenario_data["name"],
                    mode=scenario_data["mode"],
                    type=scenario_data["type"],
                    text=scenario_data["text"],
                    metrics=scenario_data["metrics"],
                    response=scenario_data.get("response", None),
                    community=False  # CSV scenarios are not community-submitted
                ))

            db.session.commit()
            print(f"✓ Database populated with {len(scenarios)} scenarios from CSV files.")
            return 0
        except Exception as e:
            print(f"Error populating database: {e}")
            db.session.rollback()
            return 1


if __name__ == '__main__':
    sys.exit(main())
