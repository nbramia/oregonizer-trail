import random
import json
from models import Scenario, db
from sqlalchemy.exc import SQLAlchemyError
import logging

class developmentGame:
    def __init__(self):
        from mode_config import get_default_mode
        logging.debug("Initializing game instance")
        self.difficulty = "Normal"
        self.mode = get_default_mode()
        self.variation_range = (0.8, 1.25)
        self.include_community_scenarios = False
        self.metrics = {}  # Dictionary to store metric values dynamically
        self.reset_game()

    def reset_game(self):
        logging.debug("Resetting game")
        self.set_initial_values()
        self.turns_survived = 0
        self.status = "developing"
        self.current_scenario = None
        self.last_scenario_was_informational = False
        self.setup_scenarios()

    def setup_scenarios(self):
        logging.debug("Setting up scenarios")
        
        decision_query = Scenario.query.filter_by(type='decision', mode=self.mode)
        if not self.include_community_scenarios:
            decision_query = decision_query.filter_by(community=False)
        self.decision_scenarios = decision_query.all()

        informational_query = Scenario.query.filter_by(type='informational', mode=self.mode)
        if not self.include_community_scenarios:
            informational_query = informational_query.filter_by(community=False)
        self.informational_scenarios = informational_query.all()

        random.shuffle(self.decision_scenarios)
        random.shuffle(self.informational_scenarios)
        self.decision_scenarios_queue = self.decision_scenarios[:]
        self.informational_scenarios_queue = self.informational_scenarios[:]
        
        logging.debug(f"Loaded {len(self.decision_scenarios_queue)} decision scenarios, {len(self.informational_scenarios_queue)} informational scenarios")

    def set_include_community_scenarios(self, include):
        logging.debug(f"Setting include_community_scenarios to {include}")
        self.include_community_scenarios = include
        self.reset_game()

    def set_initial_values(self):
        from mode_config import get_mode_metrics
        logging.debug(f"Setting initial values for difficulty: {self.difficulty}")

        # Get metrics for current mode
        mode_metrics = get_mode_metrics(self.mode)

        # Set initial values based on difficulty
        if self.difficulty == "Normal":
            initial_value = 100
        elif self.difficulty == "Hard":
            initial_value = 85
        elif self.difficulty == "Crazy":
            initial_value = 75
        else:
            initial_value = 100

        # Special case for tech_debt in Hard/Crazy modes
        tech_debt_value = initial_value
        if self.difficulty == "Hard":
            tech_debt_value = 75
        elif self.difficulty == "Crazy":
            tech_debt_value = 50

        # Initialize all metrics for the current mode
        self.metrics = {}
        for metric in mode_metrics:
            if metric == 'tech_debt':
                self.metrics[metric] = tech_debt_value
            else:
                self.metrics[metric] = initial_value

        # Also set as attributes for backwards compatibility
        for metric, value in self.metrics.items():
            setattr(self, metric, value)

    def set_difficulty(self, difficulty):
        logging.debug(f"Setting difficulty to {difficulty}")
        self.difficulty = difficulty
        if difficulty == "Normal":
            self.variation_range = (0.8, 1.25)
        elif difficulty == "Hard":
            self.variation_range = (1.0, 1.4)
        elif difficulty == "Crazy":
            self.variation_range = (1.1, 1.6)
        else:
            self.variation_range = (0.8, 1.25)
        self.set_initial_values()

    def set_mode(self, mode):
        logging.debug(f"Setting mode to {mode}")
        self.mode = mode
        self.reset_game()

    def apply_variation(self, value):
        return int(value * random.uniform(*self.variation_range))

    def update_metrics(self):
        result = {"turns_survived": self.turns_survived}
        result.update(self.metrics)
        return result

    def check_status(self):
        from mode_config import get_metric_display_name
        # Check for failures FIRST - they take absolute priority over wins
        failures = []

        # Failure messages for different metrics
        failure_messages = {
            'staff_retention': "STAFF RETENTION: Too many key staff have left the organization.<br><br>We no longer have the institutional knowledge to operate at the same scale.",
            'partner_growth': "PARTNER GROWTH: We're not making enough progress toward our vision to justify our costs.",
            'partner_retention': "PARTNER RETENTION: Too many partners have chosen not to renew their contracts.<br><br>We're not driving enough impact to justify our costs.",
            'tech_debt': "TECH DEBT: Our technical systems are starting to fail.<br><br>We can no longer safely operate at scale.",
            'revenue': "REVENUE: We aren't generating enoough revenue.<br><br>We can no longer sustain operations.",
            'net_votes': "NET VOTES: We're not making enough progress toward our mission to justify our costs."
        }

        # Check each metric for failure
        for metric, value in self.metrics.items():
            if value <= 0:
                message = failure_messages.get(metric, f"{get_metric_display_name(metric)} has reached zero.")
                failures.append(message)

        # If any failures exist, return failure message immediately
        if failures:
            if len(failures) == 1:
                return f"<br>Failure.<br><br>{failures[0]}"
            else:
                failure_text = "<br><br>".join(failures)
                return f"<br>Failure.<br><br>Multiple critical issues have ended your journey:<br><br>{failure_text}"

        # Only check win conditions if there are NO failures
        # Check thriving: all non-tech_debt metrics at 100
        non_tech_metrics = [v for k, v in self.metrics.items() if k != 'tech_debt']
        if self.turns_survived >= 10 and all(v >= 100 for v in non_tech_metrics):
            return "Congratulations!<br><br>Well into the game, all key metrics are at 100.<br><br>You're thriving!"

        # Check survival (25 turns)
        if self.turns_survived >= 25:
            return "Congratulations!<br><br>You've survived 25 turns and avoided any major issues."

        # No end condition met - game continues
        return None

    def adjust_for_tech_debt(self):
        logging.debug("Calling adjust_for_tech_debt")

        # Only adjust tech debt if it exists in current mode's metrics
        if 'tech_debt' not in self.metrics:
            return

        # Calculate debt factor based on available metrics
        # For Product Development/Partnership modes: use partner metrics
        # For Movement Labs: use revenue and net_votes
        if 'partner_growth' in self.metrics and 'partner_retention' in self.metrics:
            debt_factor = round((self.metrics['partner_growth'] + self.metrics['partner_retention']) / 200)
        elif 'revenue' in self.metrics and 'net_votes' in self.metrics:
            debt_factor = round((self.metrics['revenue'] + self.metrics['net_votes']) / 200)
        else:
            debt_factor = 0

        old_tech_debt = self.metrics['tech_debt']
        self.metrics['tech_debt'] = max(0, self.metrics['tech_debt'] - debt_factor)
        self.tech_debt = self.metrics['tech_debt']  # Update attribute for backwards compatibility
        logging.debug(f"Adjusted for tech debt: old_tech_debt={old_tech_debt}, debt_factor={debt_factor}, new_tech_debt={self.metrics['tech_debt']}")

    def next_turn(self):
        logging.debug("Proceeding to next turn")
        self.turns_survived += 1
        self.adjust_for_tech_debt()

        # Initialize messages as an empty list to avoid undefined variable errors
        messages = []

        selected_scenario = self.get_scenario()
        if selected_scenario:
            messages.append(selected_scenario.text)
            if selected_scenario.type == 'informational':
                metrics_changes = json.loads(selected_scenario.metrics)
                for metric, change in metrics_changes.items():
                    self.apply_metric_change(metric, change)

        status_message = self.check_status()
        logging.debug(f"Messages to be sent to frontend: {messages}")
        logging.debug(f"Status message to be sent to frontend: {status_message}")
        return messages, status_message

    def get_scenario(self):
        if not self.decision_scenarios_queue and not self.informational_scenarios_queue:
            self.setup_scenarios()

        # Determine if we should show informational scenario
        # Rules: Never on turn 1, never twice in a row, 20% probability otherwise
        can_show_informational = (
            self.turns_survived > 1 and  # Not turn 1 (turn counter incremented before this)
            not self.last_scenario_was_informational and  # Not twice in a row
            self.informational_scenarios_queue and  # Queue not empty
            random.random() < 0.20  # 20% chance
        )

        if can_show_informational:
            # Show informational scenario
            self.current_scenario = self.informational_scenarios_queue.pop(0)
            self.last_scenario_was_informational = True
            if not self.informational_scenarios_queue:
                self.informational_scenarios_queue = self.informational_scenarios[:]
                random.shuffle(self.informational_scenarios_queue)
        else:
            # Show decision scenario
            self.current_scenario = self.decision_scenarios_queue.pop(0)
            self.last_scenario_was_informational = False
            if not self.decision_scenarios_queue:
                self.decision_scenarios_queue = self.decision_scenarios[:]
                random.shuffle(self.decision_scenarios_queue)

        logging.debug(f"Selected scenario: {self.current_scenario.name} (type: {self.current_scenario.type})")
        return self.current_scenario

    def handle_scenario(self, scenario_name, action):
        logging.debug(f"Handling scenario: {scenario_name} with action: {action}")
        scenario = Scenario.query.filter_by(name=scenario_name).first()
        if not scenario:
            raise ValueError(f"Scenario {scenario_name} not found in the database")

        metrics_changes = json.loads(scenario.metrics).get(action)
        response_text = json.loads(scenario.response).get(action)

        if metrics_changes:
            for metric, change in metrics_changes.items():
                self.apply_metric_change(metric, change)

        # Convert newlines to HTML breaks for display
        if response_text:
            response_text = response_text.replace('\n', '<br>')

        return response_text

    def apply_metric_change(self, metric, change):
        if metric in self.metrics:
            self.metrics[metric] += self.apply_variation(change)
            # Clamp metric to 0-100 range
            self.metrics[metric] = max(min(self.metrics[metric], 100), 0)
            # Also update as attribute for backwards compatibility
            setattr(self, metric, self.metrics[metric])
        else:
            logging.warning(f"Attempted to change metric '{metric}' which is not in current mode's metrics")
