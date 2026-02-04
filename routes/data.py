"""
Data routes blueprint
Handles data retrieval endpoints (user info, leaderboard, modes, metrics)
"""
import logging
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import User

# Create blueprint
data_bp = Blueprint('data', __name__)

@data_bp.route('/get_user_info')
@login_required
def get_user_info():
    """Get current user's information"""
    try:
        user_info = {
            'email': current_user.email,
            'high_score': current_user.high_score,
            'games_played': current_user.games_played,
            'last_game_played': current_user.last_game_played
        }
        return jsonify(user_info), 200
    except Exception as e:
        logging.error(f"Error in /get_user_info: {e}")
        return jsonify({"error": str(e)}), 500

@data_bp.route('/get_leaderboard')
@login_required
def get_leaderboard():
    """Get top 10 users by high score"""
    try:
        logging.debug("Accessing /get_leaderboard")
        users = User.query.filter(User.high_score > 0).order_by(User.high_score.desc()).limit(10).all()
        logging.debug(f"Fetched users: {users}")
        leaderboard = [{'email': user.email, 'high_score': user.high_score} for user in users]
        logging.debug(f"Leaderboard data: {leaderboard}")
        return jsonify(leaderboard), 200
    except Exception as e:
        logging.error(f"Error in /get_leaderboard: {e}")
        return jsonify({"error": str(e)}), 500

@data_bp.route('/get_modes', methods=['GET'])
@login_required
def get_modes():
    """Get list of enabled game modes"""
    from mode_config import get_enabled_modes, get_default_mode
    try:
        # Return only enabled modes from configuration
        modes_list = get_enabled_modes()
        default_mode = get_default_mode()
        return jsonify({"modes": modes_list, "default_mode": default_mode}), 200
    except Exception as e:
        logging.error(f"Error fetching modes: {e}")
        return jsonify({"error": str(e)}), 500

@data_bp.route('/get_mode_metrics', methods=['GET'])
@login_required
def get_mode_metrics_endpoint():
    """Get metrics configuration for a specific mode"""
    from app import get_game
    from mode_config import get_mode_metrics, get_metric_display_name
    try:
        mode = request.args.get('mode', get_game().mode)
        metrics = get_mode_metrics(mode)

        # Return both internal keys and display names
        metrics_info = [
            {'key': metric, 'display': get_metric_display_name(metric)}
            for metric in metrics
        ]

        return jsonify({"metrics": metrics_info}), 200
    except Exception as e:
        logging.error(f"Error fetching mode metrics: {e}")
        return jsonify({"error": str(e)}), 500
