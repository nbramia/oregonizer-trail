"""
Game routes blueprint
Handles game state management, turns, scenarios, and game ending
"""
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, Scenario
from validation import (
    validate_difficulty, validate_turns_survived, validate_metric_value,
    ValidationError
)

# Create blueprint
game_bp = Blueprint('game', __name__)

@game_bp.route('/reset_game', methods=['POST'])
@login_required
def reset_game():
    """Reset the game to initial state"""
    from app import get_game
    try:
        logging.debug("Resetting game")
        # Reset the existing game instance (preserves difficulty/mode settings)
        game = get_game()
        game.reset_game()
        metrics = game.update_metrics()
        logging.debug(f"Game reset: {metrics}")
        return jsonify({"metrics": metrics})
    except Exception as e:
        logging.error(f"Error in /reset_game: {e}")
        return jsonify({"error": str(e)}), 500

@game_bp.route('/next_turn', methods=['POST'])
def next_turn():
    """Process next game turn and return new scenario"""
    from app import get_game
    try:
        logging.debug("Processing next turn...")
        messages, status_message = get_game().next_turn()
        scenario = get_game().current_scenario

        # Check if the user has reached Turn 2
        if get_game().turns_survived == 2:
            if current_user.is_authenticated:
                try:
                    logging.debug(f"Incrementing games_started for user {current_user.email}")
                    if current_user.games_started is None:
                        current_user.games_started = 0
                    current_user.games_started += 1
                    db.session.commit()  # Ensure this change is committed to the database
                except Exception as db_error:
                    logging.error(f"Database commit error: {db_error}")
                    return jsonify({"error": "Database commit error"}), 500
            else:
                logging.warning("User not authenticated, cannot increment games_started")

        # Correctly create the response dictionary with necessary attributes
        scenario_data = {
            "scenario": scenario.name if scenario else None,
            "scenario_id": scenario.id if scenario else None,
            "scenario_text": scenario.text if scenario else None,
            "is_decision": scenario.type == 'decision' if scenario else False,
            "metrics": get_game().update_metrics(),
            "messages": messages if messages else [],  # Ensure messages is always defined
            "is_community": scenario.community if scenario else False
        }

        if status_message:
            scenario_data["status_message"] = status_message

        logging.debug(f"Returning scenario data: {scenario_data}")
        return jsonify(scenario_data)
    except Exception as e:
        logging.error(f"Unexpected error in /next_turn: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500

@game_bp.route('/handle_scenario', methods=['POST'])
def handle_scenario():
    """Handle user's response to a scenario"""
    from app import get_game
    try:
        data = request.get_json()
        scenario_id = data['scenario']
        action = data['action']
        logging.debug(f"Handling scenario: {scenario_id} with action: {action}")

        # Retrieve the scenario from the database using the ID
        scenario = Scenario.query.get(scenario_id)
        if not scenario:
            logging.error(f"Scenario {scenario_id} not found in the database")
            return jsonify({"error": f"Scenario {scenario_id} not found in the database"}), 500

        response_text = get_game().handle_scenario(scenario.name, action)
        metrics = get_game().update_metrics()
        status_message = get_game().check_status()

        response_data = {
            "metrics": metrics,
            "message": response_text
        }

        if status_message:
            response_data["status_message"] = status_message

        return jsonify(response_data)
    except Exception as e:
        logging.error(f"Unexpected error in /handle_scenario: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500

@game_bp.route('/end_game', methods=['POST'])
@login_required
def end_game():
    """End the game and calculate final score"""
    from app import get_game
    from mode_config import get_mode_metrics

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body must be JSON"}), 400

        # Validate required fields
        turns_survived = data.get('turns_survived')
        difficulty = data.get('difficulty', 'Normal')
        won_game = data.get('won', False)

        try:
            turns_survived = validate_turns_survived(turns_survived)
            difficulty = validate_difficulty(difficulty)
        except ValidationError as e:
            logging.warning(f"Validation error in /end_game: {e}")
            return jsonify({"error": str(e)}), 400

        # Get current mode metrics to handle dynamic metrics
        current_metrics = get_mode_metrics(get_game().mode)

        # Collect and validate all metric values from request
        metrics_values = {}
        for metric in current_metrics:
            value = data.get(metric)
            if value is not None:
                try:
                    metrics_values[metric] = validate_metric_value(value, metric)
                except ValidationError as e:
                    logging.warning(f"Validation error for metric {metric}: {e}")
                    return jsonify({"error": str(e)}), 400
            else:
                # Default to 0 if metric not provided
                metrics_values[metric] = 0

        # Calculate Difficulty score
        if difficulty == 'Normal':
            difficulty_score = 50
        elif difficulty == 'Hard':
            difficulty_score = 75
        else:  # 'Crazy'
            difficulty_score = 100

        # Calculate Turns score (proportional to turns survived out of 25)
        turns_score = min((turns_survived / 25) * 100, 100)

        # Calculate Win bonus (binary: 100 if won, 0 if lost)
        win_bonus = 100 if won_game else 0

        # Calculate Points score from all metrics (excluding tech_debt if present)
        non_tech_metrics = [v for k, v in metrics_values.items() if k != 'tech_debt']
        if non_tech_metrics:
            total_points = sum(non_tech_metrics)
            points_score = total_points / len(non_tech_metrics)
        else:
            total_points = 0
            points_score = 0

        # Clamp metrics to 0-100 for score calculation
        for metric in metrics_values:
            metrics_values[metric] = max(min(metrics_values[metric], 100), 0)

        # Recalculate total_points after clamping
        non_tech_metrics = [v for k, v in metrics_values.items() if k != 'tech_debt']
        total_points = sum(non_tech_metrics) if non_tech_metrics else 0
        points_score = total_points / 4

        # Calculate overall score with weighted components:
        # - Difficulty: 40% weight (2x)
        # - Turns: 20% weight (1x) - proportional to turns/25
        # - Win Bonus: 20% weight (1x) - binary 0 or 100
        # - Points: 20% weight (1x) - average of metrics
        overall_score = (2 * difficulty_score + turns_score + win_bonus + points_score) / 5

        # Update high score if the new overall score is higher
        if overall_score > current_user.high_score:
            current_user.high_score = overall_score

        # Increment games_played and update last_game_played
        current_user.games_played += 1
        current_user.last_game_played = datetime.utcnow()

        db.session.commit()
        logging.debug(f"Updated high score for user {current_user.email} to {current_user.high_score}")
        logging.debug(f"Games played for user {current_user.email}: {current_user.games_played}")
        logging.debug(f"Last game played for user {current_user.email}: {current_user.last_game_played}")

        # Get the status message from the game logic
        status_message = get_game().check_status()  # Ensure this function returns the appropriate status message

        # Build scores response with dynamic metrics
        scores_response = {
            "difficulty": difficulty,
            "difficulty_score": difficulty_score,
            "turns_survived": turns_survived,
            "turns_score": turns_score,
            "won_game": won_game,
            "win_bonus": win_bonus,
            "total_points": total_points,
            "points_score": points_score,
            "overall_score": overall_score
        }
        # Add all current mode metrics to the response
        scores_response.update(metrics_values)

        return jsonify({
            "message": "Game ended successfully",
            "status_message": status_message,
            "high_score": current_user.high_score,
            "scores": scores_response
        }), 200
    except Exception as e:
        logging.error(f"Error in /end_game: {e}")
        return jsonify({"error": str(e)}), 500
