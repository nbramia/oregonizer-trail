"""
Scenarios routes blueprint
Handles scenario creation and management
"""
import json
import logging
from flask import Blueprint, request, jsonify
from flask_login import login_required
from models import db, Scenario
from validation import (
    validate_scenario_name, validate_scenario_mode, validate_scenario_type,
    validate_scenario_text, validate_scenario_metrics, validate_scenario_response,
    ValidationError
)

# Create blueprint
scenarios_bp = Blueprint('scenarios', __name__)

@scenarios_bp.route('/create_scenario', methods=['POST'])
@login_required
def create_scenario():
    """Create a new community scenario"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body must be JSON"}), 400

        logging.debug(f"Received data for new scenario: {data}")

        # Validate required fields
        try:
            name = validate_scenario_name(data.get('name'))
            mode = validate_scenario_mode(data.get('mode'))
            type = validate_scenario_type(data.get('type'))
            text = validate_scenario_text(data.get('text'))
            metrics = data.get('metrics')
            response = data.get('response', None)

            # Validate metrics (as JSON string)
            if isinstance(metrics, dict):
                # If it's already a dict, convert to JSON string for validation
                metrics = json.dumps(metrics)
            metrics = validate_scenario_metrics(metrics, type, mode)

            # Validate response if it's a decision scenario
            if type == 'decision':
                if isinstance(response, dict):
                    response = json.dumps(response)
                response = validate_scenario_response(response, type)

        except ValidationError as e:
            logging.warning(f"Validation error in /create_scenario: {e}")
            return jsonify({"error": str(e)}), 400

        logging.debug(f"Validated scenario data: name={name}, mode={mode}, type={type}")

        # Check if a scenario with the same name already exists
        existing_scenario = Scenario.query.filter_by(name=name).first()
        if existing_scenario:
            return jsonify({"error": "A scenario with this name already exists."}), 400

        logging.debug(f"Serialized metrics: {metrics}")

        scenario = Scenario(
            name=name,
            mode=mode,
            type=type,
            text=text,
            metrics=metrics,  # Already a JSON string from validation
            response=response if response else None,  # Already a JSON string or None
            community=True
        )

        db.session.add(scenario)
        db.session.commit()
        logging.debug("Scenario created successfully.")
        return jsonify({"message": "Scenario created successfully."}), 200
    except Exception as e:
        logging.error(f"Error creating scenario: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
