"""
Settings routes blueprint
Handles game settings (difficulty, mode, community scenarios)
"""
import logging
from flask import Blueprint, request, jsonify
from flask_login import login_required
from mode_config import get_default_mode, validate_mode
from validation import validate_difficulty, ValidationError

# Create blueprint
settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/set_difficulty', methods=['POST'])
@login_required
def set_difficulty():
    """Set game difficulty level"""
    from app import get_game
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body must be JSON"}), 400

        difficulty = data.get('difficulty', 'Normal')

        # Validate difficulty
        try:
            difficulty = validate_difficulty(difficulty)
        except ValidationError as e:
            logging.warning(f"Validation error in /set_difficulty: {e}")
            return jsonify({"error": str(e)}), 400

        logging.debug(f"Setting difficulty: {difficulty}")
        get_game().set_difficulty(difficulty)
        metrics = get_game().update_metrics()
        logging.debug(f"Difficulty set: {metrics}")
        return jsonify({"message": f"Difficulty set to {difficulty}", "metrics": metrics}), 200
    except Exception as e:
        logging.error(f"Error in /set_difficulty: {e}")
        return jsonify({"error": str(e)}), 500

@settings_bp.route('/set_mode', methods=['POST'])
@login_required
def set_mode():
    """Set game mode"""
    from app import get_game
    try:
        data = request.get_json()
        mode = data.get('mode', get_default_mode())
        logging.debug(f"Setting mode: {mode}")

        # Validate mode is enabled
        try:
            validate_mode(mode)
        except ValueError as e:
            logging.error(f"Invalid mode: {e}")
            return jsonify({"error": str(e)}), 400

        get_game().set_mode(mode)
        metrics = get_game().update_metrics()
        logging.debug(f"Mode set: {metrics}")
        return jsonify({"message": f"Mode set to {mode}", "metrics": metrics}), 200
    except Exception as e:
        logging.error(f"Error in /set_mode: {e}")
        return jsonify({"error": str(e)}), 500

@settings_bp.route('/set_include_community_scenarios', methods=['POST'])
def set_include_community_scenarios():
    """Toggle inclusion of community-created scenarios"""
    from app import get_game
    try:
        data = request.get_json()
        include = data.get('include')
        if include is None:
            return jsonify({"error": "Invalid input"}), 400

        logging.debug(f"Received request to set include_community_scenarios to {include}")
        get_game().set_include_community_scenarios(include)
        return jsonify({"message": "Include community scenarios setting updated successfully"})
    except Exception as e:
        logging.error(f"Error setting include community scenarios: {e}")
        return jsonify({"error": "Internal Server Error"}), 500
