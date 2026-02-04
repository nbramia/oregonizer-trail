"""
Input validation for API endpoints
"""
from functools import wraps
from flask import request, jsonify
import json
import logging


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


def validate_difficulty(difficulty):
    """Validate difficulty value"""
    valid_difficulties = ['Normal', 'Hard', 'Crazy']
    if difficulty not in valid_difficulties:
        raise ValidationError(f"Invalid difficulty: {difficulty}. Must be one of {valid_difficulties}")
    return difficulty


def validate_turns_survived(turns):
    """Validate turns_survived value"""
    if not isinstance(turns, int) or turns < 0:
        raise ValidationError(f"Invalid turns_survived: {turns}. Must be a non-negative integer")
    if turns > 1000:  # Reasonable upper bound
        raise ValidationError(f"Invalid turns_survived: {turns}. Value too large")
    return turns


def validate_metric_value(value, metric_name):
    """Validate metric value (0-200 range)"""
    if not isinstance(value, (int, float)):
        raise ValidationError(f"Invalid {metric_name}: {value}. Must be a number")
    if value < 0 or value > 200:
        raise ValidationError(f"Invalid {metric_name}: {value}. Must be between 0 and 200")
    return int(value)


def validate_scenario_name(name):
    """Validate scenario name"""
    if not name or not isinstance(name, str):
        raise ValidationError("Scenario name is required and must be a string")
    if len(name) > 200:
        raise ValidationError("Scenario name too long (max 200 characters)")
    return name.strip()


def validate_scenario_mode(mode):
    """Validate scenario mode"""
    from mode_config import is_mode_enabled
    if not mode or not isinstance(mode, str):
        raise ValidationError("Mode is required and must be a string")
    if not is_mode_enabled(mode):
        raise ValidationError(f"Mode '{mode}' is not enabled")
    return mode


def validate_scenario_type(scenario_type):
    """Validate scenario type"""
    valid_types = ['decision', 'informational']
    if scenario_type not in valid_types:
        raise ValidationError(f"Invalid scenario type: {scenario_type}. Must be one of {valid_types}")
    return scenario_type


def validate_scenario_text(text):
    """Validate scenario text"""
    if not text or not isinstance(text, str):
        raise ValidationError("Scenario text is required and must be a string")
    if len(text) > 5000:
        raise ValidationError("Scenario text too long (max 5000 characters)")
    return text.strip()


def validate_scenario_metrics(metrics, scenario_type, mode):
    """Validate scenario metrics JSON"""
    from mode_config import get_mode_metrics

    if not isinstance(metrics, str):
        raise ValidationError("Metrics must be a JSON string")

    try:
        metrics_dict = json.loads(metrics)
    except json.JSONDecodeError:
        raise ValidationError("Metrics must be valid JSON")

    valid_metrics = get_mode_metrics(mode)

    if scenario_type == 'decision':
        # Decision scenarios must have 'yes' and 'no' keys
        if not isinstance(metrics_dict, dict) or 'yes' not in metrics_dict or 'no' not in metrics_dict:
            raise ValidationError("Decision scenario metrics must have 'yes' and 'no' keys")

        for action in ['yes', 'no']:
            if not isinstance(metrics_dict[action], dict):
                raise ValidationError(f"Metrics for '{action}' must be a dictionary")

            # Validate each metric key and value
            for metric_key, value in metrics_dict[action].items():
                if metric_key not in valid_metrics:
                    raise ValidationError(f"Invalid metric '{metric_key}' for mode '{mode}'")
                if not isinstance(value, (int, float)):
                    raise ValidationError(f"Metric value for '{metric_key}' must be a number")
                if value < -100 or value > 100:
                    raise ValidationError(f"Metric value for '{metric_key}' must be between -100 and 100")

    elif scenario_type == 'informational':
        # Informational scenarios have metric: value directly
        if not isinstance(metrics_dict, dict):
            raise ValidationError("Informational scenario metrics must be a dictionary")

        for metric_key, value in metrics_dict.items():
            if metric_key not in valid_metrics:
                raise ValidationError(f"Invalid metric '{metric_key}' for mode '{mode}'")
            if not isinstance(value, (int, float)):
                raise ValidationError(f"Metric value for '{metric_key}' must be a number")
            if value < -100 or value > 100:
                raise ValidationError(f"Metric value for '{metric_key}' must be between -100 and 100")

    return metrics


def validate_scenario_response(response, scenario_type):
    """Validate scenario response JSON"""
    if scenario_type == 'decision':
        if not response or not isinstance(response, str):
            raise ValidationError("Response is required for decision scenarios")

        try:
            response_dict = json.loads(response)
        except json.JSONDecodeError:
            raise ValidationError("Response must be valid JSON")

        if not isinstance(response_dict, dict) or 'yes' not in response_dict or 'no' not in response_dict:
            raise ValidationError("Decision scenario response must have 'yes' and 'no' keys")

        for action in ['yes', 'no']:
            if not isinstance(response_dict[action], str):
                raise ValidationError(f"Response for '{action}' must be a string")

    return response


def validate_request(validation_rules):
    """
    Decorator to validate request data against specified rules

    Usage:
        @validate_request({
            'difficulty': validate_difficulty,
            'turns_survived': validate_turns_survived
        })
        def my_endpoint():
            data = request.get_json()
            # data is now validated
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            try:
                data = request.get_json()
                if not data:
                    return jsonify({"error": "Request body must be JSON"}), 400

                validated_data = {}
                for field, validator in validation_rules.items():
                    if field in data:
                        try:
                            validated_data[field] = validator(data[field])
                        except ValidationError as e:
                            logging.warning(f"Validation error for field '{field}': {e}")
                            return jsonify({"error": str(e)}), 400

                # Store validated data for the endpoint to use
                request.validated_data = validated_data
                return f(*args, **kwargs)

            except Exception as e:
                logging.error(f"Unexpected validation error: {e}")
                return jsonify({"error": "Invalid request data"}), 400

        return wrapped
    return decorator
