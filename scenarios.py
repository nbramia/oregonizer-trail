import random

class Scenario:
    def __init__(self, name, mode, type, text, responses):
        self.name = name
        self.mode = mode
        self.type = type
        self.text = text
        self.responses = responses

    def get_response(self, action, game):
        if action in self.responses:
            response_func = self.responses[action]
            response_text = response_func(game)
            return response_text
        return None

    def apply_variation(self, value, variation_range):
        return int(value * random.uniform(*variation_range))

scenarios = [
    # PRODUCT DEVELOPMENT - DECISION SCENARIOS

    Scenario(
        name="feature_delay",
        mode="Product Development",
        type="decision",
        text="A feature is taking longer than anticipated.\n\nPush the team to hit the projected timeline?",
        responses={
            "yes": lambda game: (
                setattr(game, 'staff_retention', game.staff_retention - game.apply_variation(35, game.variation_range)),
                "Pushed the team to hit the deadline.<br><br>Staff retention decreased.<br><br>Partner retention held steady."
            ),
            "no": lambda game: (
                setattr(game, 'staff_retention', game.staff_retention + game.apply_variation(25, game.variation_range)),
                setattr(game, 'partner_growth', game.partner_growth - game.apply_variation(15, game.variation_range)),
                setattr(game, 'partner_retention', game.partner_retention - game.apply_variation(15, game.variation_range)),
                "Allowed delay.<br><br>Staff retention increased, partner growth and retention slightly decreased."
            )
        }
    ),
    Scenario(
        name="leadership_feature_request",
        mode="Product Development",
        type="decision",
        text="Organizational leadership makes a request for a new feature.\n\nPrioritize it?",
        responses={
            "yes": lambda game: (
                setattr(game, 'staff_retention', game.staff_retention - game.apply_variation(25, game.variation_range)),
                "Prioritized the feature.<br><br>Staff retention decreased."
            ),
            "no": lambda game: (
                "Did not prioritize the feature request.<br><br>Not much changed."
            )
        }
    ),
    Scenario(
        name="sales_feature_request",
        mode="Product Development",
        type="decision",
        text="An important partner prospect makes a request for a new feature during the sales process.\n\nPrioritize it?",
        responses={
            "yes": lambda game: (
                setattr(game, 'partner_growth', game.partner_growth + game.apply_variation(15, game.variation_range)),
                setattr(game, 'staff_retention', game.staff_retention - game.apply_variation(15, game.variation_range)),
                "Prioritized the feature.<br><br>Partner growth slightly increased.<br><br>Staff retention slightly decreased."
            ),
            "no": lambda game: (
                setattr(game, 'partner_growth', game.partner_growth - game.apply_variation(25, game.variation_range)),
                "Ignored the feature request.<br><br>The potential partner didn't sign, and they told a number of other organizations not to bother speaking to us either."
            )
        }
    ),
    Scenario(
        name="backend_issue",
        mode="Product Development",
        type="decision",
        text="Performance of the platform is degraded.\n\nPrioritize back-end improvements?",
        responses={
            "yes": lambda game: (
                setattr(game, 'partner_growth', game.partner_growth - game.apply_variation(15, game.variation_range)),
                setattr(game, 'partner_retention', game.partner_retention - game.apply_variation(15, game.variation_range)),
                setattr(game, 'tech_debt', game.tech_debt - game.apply_variation(35, game.variation_range)),
                "Prioritized backend improvements instead of working on a new feature.<br><br>Tech debt decreased, partner growth and retention slightly decreased."
            ),
            "no": lambda game: (
                setattr(game, 'tech_debt', game.tech_debt + game.apply_variation(35, game.variation_range)),
                setattr(game, 'partner_growth', game.partner_growth + game.apply_variation(15, game.variation_range)),
                "Ignored risks – built a new feature.<br><br>Tech debt increased, partner growth slightly increased."
            )
        }
    ),
    Scenario(
        name="partner_feature_request",
        mode="Product Development",
        type="decision",
        text="A current partner makes a request for a new feature.\n\nPrioritize it?",
        responses={
            "yes": lambda game: (
                setattr(game, 'partner_retention', game.partner_retention + game.apply_variation(25, game.variation_range)),
                setattr(game, 'staff_retention', game.staff_retention + game.apply_variation(15, game.variation_range)),
                setattr(game, 'partner_growth', game.partner_growth - game.apply_variation(15, game.variation_range)),
                "Prioritized partner feature request.<br><br>Partner retention increased, and staff retention slightly increased.<br><br>Partner growth slightly decreased."
            ),
            "no": lambda game: (
                setattr(game, 'partner_growth', game.partner_growth + game.apply_variation(15, game.variation_range)),
                setattr(game, 'partner_retention', game.partner_retention - game.apply_variation(20, game.variation_range)),
                "Ignored partner feature request and focused on something that prospective partners were asking for instead.<br><br>Partner retention decreased, partner growth slightly increased."
            )
        }
    ),
    Scenario(
        name="partner_change_request",
        mode="Product Development",
        type="decision",
        text="A current partner makes a request to change a current feature.\n\nPrioritize it?",
        responses={
            "yes": lambda game: (
                setattr(game, 'partner_growth', game.partner_growth - game.apply_variation(15, game.variation_range)),
                setattr(game, 'partner_retention', game.partner_retention + game.apply_variation(15, game.variation_range)),
                "Prioritized change request.<br><br>Partner retention slightly increased, partner growth slightly decreased."
            ),
            "no": lambda game: (
                setattr(game, 'partner_growth', game.partner_growth + game.apply_variation(15, game.variation_range)),
                setattr(game, 'partner_retention', game.partner_retention - game.apply_variation(15, game.variation_range)),
                "Ignored change request and worked on something new instead.<br><br>Partner retention slightly decreased, partner growth slightly increased."
            )
        }
    ),
    Scenario(
        name="cost_spike",
        mode="Product Development",
        type="decision",
        text="Costs for a core service are spiking.\n\nPrioritize changes that would control those costs?",
        responses={
            "yes": lambda game: (
                setattr(game, 'tech_debt', game.tech_debt - game.apply_variation(20, game.variation_range)),
                setattr(game, 'partner_retention', game.partner_retention - game.apply_variation(15, game.variation_range)),
                setattr(game, 'partner_growth', game.partner_growth - game.apply_variation(15, game.variation_range)),
                "Prioritized cost control.<br><br>Tech debt decreased, partner retention and growth slightly decreased."
            ),
            "no": lambda game: (
                setattr(game, 'partner_growth', game.partner_growth + game.apply_variation(15, game.variation_range)),
                setattr(game, 'tech_debt', game.tech_debt + game.apply_variation(25, game.variation_range)),
                "Ignored cost control.<br><br>Tech debt increased.<br><br>Partner growth slightly increased, which increased tech debt even more."
            )
        }
    ),
    Scenario(
        name="support_requests_spiking",
        mode="Product Development",
        type="decision",
        text="Support requests are spiking.\n\nPrioritize changes that would make the platform more intuitive?",
        responses={
            "yes": lambda game: (
                setattr(game, 'staff_retention', game.staff_retention + game.apply_variation(15, game.variation_range)),
                setattr(game, 'partner_retention', game.partner_retention + game.apply_variation(25, game.variation_range)),
                setattr(game, 'partner_growth', game.partner_growth - game.apply_variation(15, game.variation_range)),
                "Prioritized platform intuitiveness.<br><br>Staff retention and partner retention increased, partner growth slightly decreased."
            ),
            "no": lambda game: (
                setattr(game, 'partner_retention', game.partner_retention - game.apply_variation(25, game.variation_range)),
                setattr(game, 'staff_retention', game.staff_retention - game.apply_variation(15, game.variation_range)),
                "Decided not to prioritize making the platform easy to use.<br><br>Partner retention decreased and staff retention slightly decreased."
            )
        }
    ),
    Scenario(
        name="support_requests_taking_long",
        mode="Product Development",
        type="decision",
        text="Support requests are taking too long to resolve.\n\nPrioritize changes that would make it easier to diagnose and address issues?",
        responses={
            "yes": lambda game: (
                setattr(game, 'tech_debt', game.tech_debt - game.apply_variation(25, game.variation_range)),
                setattr(game, 'staff_retention', game.staff_retention + game.apply_variation(25, game.variation_range)),
                setattr(game, 'partner_retention', game.partner_retention + game.apply_variation(25, game.variation_range)),
                setattr(game, 'partner_growth', game.partner_growth - game.apply_variation(15, game.variation_range)),
                "Prioritized issue diagnosis and resolution.<br><br>Tech debt decreased, staff and partner retention increased, partner growth slightly decreased."
            ),
            "no": lambda game: (
                setattr(game, 'partner_growth', game.partner_growth + game.apply_variation(15, game.variation_range)),
                setattr(game, 'partner_retention', game.partner_retention - game.apply_variation(25, game.variation_range)),
                setattr(game, 'staff_retention', game.staff_retention - game.apply_variation(15, game.variation_range)),
                "Ignored issue diagnosis and resolution.<br><br>Partner growth increased, partner and staff retention decreased."
            )
        }
    ),
    Scenario(
        name="rest",
        mode="Product Development",
        type="decision",
        text="You just shipped a big release.\n\nDo you want your team to rest and recover, instead of immediately pushing forward?",
        responses={
            "yes": lambda game: (
                setattr(game, 'partner_growth', game.partner_growth - game.apply_variation(10, game.variation_range)),
                setattr(game, 'partner_retention', game.partner_retention - game.apply_variation(10, game.variation_range)),
                setattr(game, 'staff_retention', game.staff_retention + game.apply_variation(35, game.variation_range)),
                "Your team rested and regained their energy.<br><br>Slight decrease in partner growth and retention."
            ),
            "no": lambda game: (
                setattr(game, 'partner_growth', game.partner_growth + game.apply_variation(15, game.variation_range)),
                setattr(game, 'partner_retention', game.partner_retention + game.apply_variation(15, game.variation_range)),
                setattr(game, 'staff_retention', game.staff_retention - game.apply_variation(35, game.variation_range)),
                "Pushed forward!<br><br>Staff retention decreased, partner growth and partner retention slightly increased."
            )
        }
    ),
    # PRODUCT DEVELOPMENT - INFORMATIONAL SCENARIOS

    Scenario(
        name="aws_outage",
        mode="Product Development",
        type="informational",
        text="Amazon Web Services outage - the platform went down for 24h.\n\nPartner retention decreased.",
        responses={}
    ),
    Scenario(
        name="vendor_change",
        mode="Product Development",
        type="informational",
        text="A key vendor changed something without notice, generating a laundry list of required backend changes.\n\nTech debt increased.",
        responses={}
    ),
    Scenario(
        name="trillion_records",
        mode="Product Development",
        type="informational",
        text="A partner tried to load a trillion records - the platform went down for 2h.\n\nPartner retention slightly decreased.",
        responses={}
    ),
    Scenario(
        name="amazing_hire",
        mode="Product Development",
        type="informational",
        text="That new hire is AMAZING.\n\nStaff retention increased, and tech debt slightly decreased.",
        responses={}
    ),
    Scenario(
        name="missed_user_deadline",
        mode="Product Development",
        type="informational",
        text="You missed a deadline you'd already communicated to users.\n\nPartner retention slightly decreased.",
        responses={}
    ),
    Scenario(
        name="missed_prospect_deadline",
        mode="Product Development",
        type="informational",
        text="You missed a deadline you'd already communicated to potential new partners.\n\nPartner growth slightly decreased.",
        responses={}
    ),
    Scenario(
        name="bad_press",
        mode="Product Development",
        type="informational",
        text="Ouch, that was a rough article in the press.\n\nPartner growth and partner retention slightly decreased.",
        responses={}
    ),
    Scenario(
        name="great_press",
        mode="Product Development",
        type="informational",
        text="Wow! Great coverage in a major newspaper.\n\nPartner growth and partner retention slightly increased.",
        responses={}
    ),
    Scenario(
        name="feature_success",
        mode="Product Development",
        type="informational",
        text="Users love that new feature!\n\nPartner retention increased, and partner growth slightly increased.",
        responses={}
    ),
    # PARTNERSHIP & SUPPORT - DECISION SCENARIOS

    Scenario(
        name="support_priority_conflict",
        mode="Partnership & Support",
        type="decision",
        text="A key account has a new priority support request. \n\nPrioritize it over longer-standing requests from less critical accounts?",
        responses={
            "yes": lambda game: (
                setattr(game, 'partner_retention', game.partner_retention + game.apply_variation(15, game.variation_range)),
                setattr(game, 'partner_growth', game.partner_growth - game.apply_variation(15, game.variation_range)),
                "Prioritized support for key account.<br><br>Partner retention increased slightly.<br><br>Partner growth decreased slightly."
            ),
            "no": lambda game: (
                setattr(game, 'partner_retention', game.partner_retention - game.apply_variation(20, game.variation_range)),
                setattr(game, 'partner_growth', game.partner_growth + game.apply_variation(15, game.variation_range)),
                "Did not prioritize key account support.<br><br>Partner retention decreased.<br><br>Partner growth increased slightly."
            )
        }
    ),
    Scenario(
        name="feature_request_vs_bug_fix",
        mode="Partnership & Support",
        type="decision",
        text="You've identified a number of important bugs in the platform.\n\nPush the development team to prioritize these bugs over the new feature you've been asking for?",
        responses={
            "yes": lambda game: (
                setattr(game, 'partner_growth', game.partner_growth - game.apply_variation(20, game.variation_range)),
                setattr(game, 'tech_debt', game.tech_debt - game.apply_variation(15, game.variation_range)),
                setattr(game, 'partner_retention', game.partner_retention + game.apply_variation(15, game.variation_range)),
                "Prioritized bug fixes over the new feature.<br><br>Partner growth and tech debt decreased.<br><br>Partner retention slightly increased."
            ),
            "no": lambda game: (
                setattr(game, 'partner_growth', game.partner_growth + game.apply_variation(20, game.variation_range)),
                setattr(game, 'tech_debt', game.tech_debt + game.apply_variation(15, game.variation_range)),
                setattr(game, 'partner_retention', game.partner_retention - game.apply_variation(15, game.variation_range)),
                "Prioritized the new feature over bug fixes.<br><br>Partner growth and tech debt increased.<br><br>Partner retention slightly decreased."
            )
        }
    ),
    Scenario(
        name="customer_training_request",
        mode="Partnership & Support",
        type="decision",
        text="An existing account requests a series of trainings for their new employees, outside the scope of the partnership agreement.\n\nProvide the trainings over other team priorities?",
        responses={
            "yes": lambda game: (
                setattr(game, 'staff_retention', game.staff_retention - game.apply_variation(15, game.variation_range)),
                setattr(game, 'partner_retention', game.partner_retention + game.apply_variation(20, game.variation_range)),
                setattr(game, 'partner_growth', game.partner_growth - game.apply_variation(20, game.variation_range)),
                "Provided customer trainings.<br><br>Partner retention increased.<br><br>Staff retention and partner growth slightly decreased."
            ),
            "no": lambda game: (
                setattr(game, 'staff_retention', game.staff_retention + game.apply_variation(15, game.variation_range)),
                setattr(game, 'partner_retention', game.partner_retention - game.apply_variation(20, game.variation_range)),
                setattr(game, 'partner_growth', game.partner_growth + game.apply_variation(20, game.variation_range)),
                "Did not provide customer trainings.<br><br>Partner retention decreased.<br><br>Staff retention and partner growth slightly increased."
            )
        }
    ),
    Scenario(
        name="high_priority_bug",
        mode="Partnership & Support",
        type="decision",
        text="A new bug is stopping a partner from using a key area of the platform.\n\nAsk the team to work over the weekend to help them with a workaround?",
        responses={
            "yes": lambda game: (
                setattr(game, 'staff_retention', game.staff_retention - game.apply_variation(20, game.variation_range)),
                setattr(game, 'partner_retention', game.partner_retention + game.apply_variation(10, game.variation_range)),
                "A few team members worked through the weekend.<br><br>Staff retention decreased.<br><br>Partner retention slightly increased."
            ),
            "no": lambda game: (
                setattr(game, 'staff_retention', game.staff_retention + game.apply_variation(10, game.variation_range)),
                setattr(game, 'partner_retention', game.partner_retention - game.apply_variation(20, game.variation_range)),
                "The partner's program had to be delayed.<br><br>Staff retention slightly increased.<br><br>Partner retention decreased."
            )
        }
    ),
    Scenario(
        name="customization_request",
        mode="Partnership & Support",
        type="decision",
        text="A partner requested a custom tweak to a feature, specific to their use case.\n\nAsk the development team to prioritize it?",
        responses={
            "yes": lambda game: (
                setattr(game, 'partner_retention', game.partner_retention + game.apply_variation(10, game.variation_range)),
                setattr(game, 'tech_debt', game.tech_debt + game.apply_variation(25, game.variation_range)),
                setattr(game, 'partner_growth', game.partner_growth - game.apply_variation(10, game.variation_range)),
                "Prioritized partner-specific change.<br><br>Partner retention slightly increased.<br><br>Tech debt increased.<br><br>Partner growth slightly decreased."
            ),
            "no": lambda game: (
                setattr(game, 'partner_retention', game.partner_retention - game.apply_variation(10, game.variation_range)),
                setattr(game, 'tech_debt', game.tech_debt - game.apply_variation(10, game.variation_range)),
                setattr(game, 'partner_growth', game.partner_growth + game.apply_variation(10, game.variation_range)),
                "Did not prioritize partner-specific change.<br><br>Partner retention slightly decreased.<br><br>Tech debt slightly decreased.<br><br>Partner growth slightly increased."
            )
        }
    ),
    Scenario(
        name="support_team_workload",
        mode="Partnership & Support",
        type="decision",
        text="The team is struggling to keep up with the volume of support issues and requests.\n\nAsk the development team to prioritize stability and robustness over new features?",
        responses={
            "yes": lambda game: (
                setattr(game, 'partner_retention', game.partner_retention + game.apply_variation(10, game.variation_range)),
                setattr(game, 'partner_growth', game.partner_growth - game.apply_variation(10, game.variation_range)),
                setattr(game, 'staff_retention', game.staff_retention + game.apply_variation(20, game.variation_range)),
                "Support demand decreased as a result of the focus on stability.<br><br>Staff retention increased, and partner retention slightly increased.<br><br>Partner growth slightly decreased."
            ),
            "no": lambda game: (
                setattr(game, 'partner_retention', game.partner_retention - game.apply_variation(10, game.variation_range)),
                setattr(game, 'partner_growth', game.partner_growth + game.apply_variation(10, game.variation_range)),
                setattr(game, 'staff_retention', game.staff_retention - game.apply_variation(20, game.variation_range)),
                "Support demand continued to increase.<br><br>Staff retention decreased, and partner retention slightly decreased.<br><br>Partner growth slightly increased."
            )
        }
    ),
    Scenario(
        name="renewal_discount_request",
        mode="Partnership & Support",
        type="decision",
        text="A current partner is requesting a significant renewal discount.\n\nProvide the discount?",
        responses={
            "yes": lambda game: (
                setattr(game, 'staff_retention', game.staff_retention - game.apply_variation(20, game.variation_range)),
                setattr(game, 'partner_retention', game.partner_retention + game.apply_variation(10, game.variation_range)),
                "Provided renewal discount; the budget no longer supports hiring a new team member.<br><br>Staff retention decreased.<br><br>Partner retention slightly increased."
            ),
            "no": lambda game: (
                setattr(game, 'staff_retention', game.staff_retention + game.apply_variation(20, game.variation_range)),
                setattr(game, 'partner_retention', game.partner_retention - game.apply_variation(10, game.variation_range)),
                "Did not provide renewal discount; the budget supports hiring a new team member.<br><br>Staff retention increased.<br><br>Partner retention slightly decreased."
            )
        }
    ),
    Scenario(
        name="customer_feedback_incorporation",
        mode="Partnership & Support",
        type="decision",
        text="Current partners are requesting very different features than potential new partners.\n\nPrioritize the feedback and input of current customers over those of potential new partners?",
        responses={
            "yes": lambda game: (
                setattr(game, 'partner_retention', game.partner_retention + game.apply_variation(20, game.variation_range)),
                setattr(game, 'partner_growth', game.partner_growth - game.apply_variation(10, game.variation_range)),
                "Prioritized the input of current partners over that of potential new partners.<br><br>Partner retention increased.<br><br>Partner growth slightly decreased."
            ),
            "no": lambda game: (
                setattr(game, 'partner_retention', game.partner_retention - game.apply_variation(20, game.variation_range)),
                setattr(game, 'partner_growth', game.partner_growth + game.apply_variation(10, game.variation_range)),
                "Prioritized the input of potential new partners over that of current partners.<br><br>Partner retention decreased.<br><br>Partner growth slightly increased."
            )
        }
    ),
    Scenario(
        name="support_request_surge",
        mode="Partnership & Support",
        type="decision",
        text="Support requests are surging.\n\nTake a step back to improve processes and systems, at the expense of responsiveness to current requests?",
        responses={
            "yes": lambda game: (
                setattr(game, 'staff_retention', game.staff_retention + game.apply_variation(25, game.variation_range)),
                setattr(game, 'partner_retention', game.partner_retention - game.apply_variation(20, game.variation_range)),
                "Took a step back and focused on process.<br><br>Staff retention increased.<br><br>Partner retention decreased."
            ),
            "no": lambda game: (
                setattr(game, 'staff_retention', game.staff_retention - game.apply_variation(15, game.variation_range)),
                setattr(game, 'partner_retention', game.partner_retention + game.apply_variation(15, game.variation_range)),
                "Prioritized responsiveness to current requests.<br><br>Staff retention slightly decreased.<br><br>Partner retention slightly increased."
            )
        }
    ),

    # PARTNERSHIP & SUPPORT - INFORMATIONAL SCENARIOS

    Scenario(
        name="major_outage",
        mode="Partnership & Support",
        type="informational",
        text="There was a major outage.\n\nPartner retention decreased.",
        responses={}
    ),
    Scenario(
        name="key_customer_churn",
        mode="Partnership & Support",
        type="informational",
        text="A key customer – one tightly aligned with our organization's identity and mission – decided not to renew their contract.\n\nPartner retention slightly decreased and staff retention decreased.",
        responses={}
    ),
    Scenario(
        name="unexpected_uptime",
        mode="Partnership & Support",
        type="informational",
        text="The platform has had a prolonged period of 100% uptime.\n\nPartner retention slightly increased.",
        responses={}
    ),
    Scenario(
        name="high_support_rating",
        mode="Partnership & Support",
        type="informational",
        text="Your support team is getting great feedback from partners.\n\nPartner retention increased, and that reputation drove an increase in partner growth.",
        responses={}
    ),
    Scenario(
        name="renewal_rush",
        mode="Partnership & Support",
        type="informational",
        text="A large number of partners' contracts are up for renewal, and the team has been underwater.\n\nStaff retention decreased.",
        responses={}
    ),
    Scenario(
        name="negative_feedback",
        mode="Partnership & Support",
        type="informational",
        text="A key customer spoke publicly about a bad experience with the platform.\n\nPartner retention and growth decreased.",
        responses={}
    ),
    Scenario(
        name="positive_testimonial",
        mode="Partnership & Support",
        type="informational",
        text="A partner gave us a strong testimonial to feature on the website.\n\nPartner growth increased.",
        responses={}
    ),
    Scenario(
        name="new_competitor",
        mode="Partnership & Support",
        type="informational",
        text="Another organization has entered the market.\n\nPartner retention and growth decreased.",
        responses={}
    ),
    Scenario(
        name="unexpected_budget_increase",
        mode="Partnership & Support",
        type="informational",
        text="You received an unexpected budget increase and were able to hire staff to do new account development.\n\nPartner growth increased.",
        responses={}
    )
]

def get_scenario(name):
    for scenario in scenarios:
        if scenario.name == name:
            return scenario
    return None
