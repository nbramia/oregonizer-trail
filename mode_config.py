"""
Mode Configuration

This file controls which game modes are available in the application.
To enable/disable modes, simply set the 'enabled' flag to True/False.

The 'default' flag determines which mode is selected when a new game starts.
Only ONE mode should have default=True.
"""

# Available game modes
# Format: {
#   'name': 'Mode Name',           # Display name shown to users
#   'enabled': True/False,         # Whether this mode is active
#   'default': True/False,         # Whether this is the default mode
#   'description': 'Description'   # Optional description
# }

MODES = [
    {
        'name': 'Product Development',
        'enabled': False,  # Temporarily disabled
        'default': False,
        'description': 'Scenarios focused on feature prioritization, technical debt, team capacity, and product roadmap decisions',
        'metrics': ['staff_retention', 'partner_retention', 'partner_growth', 'tech_debt']
    },
    {
        'name': 'Partnership & Support',
        'enabled': False,  # Temporarily disabled
        'default': False,
        'description': 'Scenarios centered on customer relationships, support operations, renewal strategies, and stakeholder management',
        'metrics': ['staff_retention', 'partner_retention', 'partner_growth', 'tech_debt']
    },
    {
        'name': 'Movement Labs',
        'enabled': True,
        'default': True,  # Now the default (and only enabled) mode
        'description': 'Scenarios focused on movement building, community engagement, and organizational growth',
        'metrics': ['staff_retention', 'revenue', 'net_votes', 'tech_debt']
    }
]


def get_enabled_modes():
    """
    Returns list of enabled mode names.

    Returns:
        list: Names of enabled modes
    """
    return [mode['name'] for mode in MODES if mode['enabled']]


def get_default_mode():
    """
    Returns the default mode name.

    Returns:
        str: Name of default mode, or first enabled mode if no default set
    """
    # Find mode marked as default
    default_modes = [mode['name'] for mode in MODES if mode.get('default', False) and mode['enabled']]

    if default_modes:
        return default_modes[0]

    # Fallback to first enabled mode
    enabled = get_enabled_modes()
    return enabled[0] if enabled else 'Product Development'


def get_mode_description(mode_name):
    """
    Returns description for a given mode.

    Args:
        mode_name (str): Name of the mode

    Returns:
        str: Description of the mode, or empty string if not found
    """
    for mode in MODES:
        if mode['name'] == mode_name:
            return mode.get('description', '')
    return ''


def is_mode_enabled(mode_name):
    """
    Check if a mode is enabled.

    Args:
        mode_name (str): Name of the mode to check

    Returns:
        bool: True if mode is enabled, False otherwise
    """
    for mode in MODES:
        if mode['name'] == mode_name:
            return mode['enabled']
    return False


def validate_mode(mode_name):
    """
    Validate that a mode name is enabled.

    Args:
        mode_name (str): Name of the mode to validate

    Returns:
        str: The mode name if valid and enabled

    Raises:
        ValueError: If mode is not enabled or doesn't exist
    """
    if not is_mode_enabled(mode_name):
        enabled = get_enabled_modes()
        raise ValueError(f"Mode '{mode_name}' is not available. Enabled modes: {enabled}")

    return mode_name


def get_mode_metrics(mode_name):
    """
    Get the list of metrics for a specific mode.

    Args:
        mode_name (str): Name of the mode

    Returns:
        list: List of metric names for the mode
    """
    for mode in MODES:
        if mode['name'] == mode_name:
            return mode.get('metrics', ['staff_retention', 'partner_retention', 'partner_growth', 'tech_debt'])
    # Default fallback
    return ['staff_retention', 'partner_retention', 'partner_growth', 'tech_debt']


def get_metric_display_name(metric_key):
    """
    Get human-readable display name for a metric.

    Args:
        metric_key (str): Internal metric key (e.g., 'staff_retention')

    Returns:
        str: Display name (e.g., 'Staff Retention')
    """
    display_names = {
        'staff_retention': 'Staff Retention',
        'partner_retention': 'Partner Retention',
        'partner_growth': 'Partner Growth',
        'tech_debt': 'Tech Debt',
        'revenue': 'Revenue',
        'net_votes': 'Net Votes'
    }
    return display_names.get(metric_key, metric_key.replace('_', ' ').title())
