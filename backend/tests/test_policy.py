from app.models import Protocol
from app.simulation.policy import evaluate_access, evaluation_order
from tests.factories import ZONE_A, ZONE_B, policy, rule

HTTPS, SQL, SSH = Protocol.HTTPS, Protocol.SQL, Protocol.SSH


def test_empty_policy_denies_by_default():
    decision = evaluate_access(policy(), ZONE_A, ZONE_B, HTTPS)
    assert not decision.allowed
    assert decision.default_applied
    assert decision.matched_rule_id is None
    assert decision.reason == "Denied by default: no rule matches zone-a → zone-b over https."


def test_default_deny_when_only_other_traffic_is_allowed():
    p = policy(rule("allow-sql", 100, "allow", ZONE_A, ZONE_B, SQL))
    assert not evaluate_access(p, ZONE_A, ZONE_B, HTTPS).allowed  # wrong protocol
    assert not evaluate_access(p, ZONE_B, ZONE_A, SQL).allowed  # wrong direction


def test_matching_allow_rule_permits_and_explains():
    p = policy(rule("allow-sql", 100, "allow", ZONE_A, ZONE_B, SQL))
    decision = evaluate_access(p, ZONE_A, ZONE_B, SQL)
    assert decision.allowed
    assert decision.matched_rule_id == "allow-sql"
    assert not decision.default_applied
    assert "Allowed by rule 'allow-sql' (priority 100)" in decision.reason


def test_matching_deny_rule_denies_and_explains():
    p = policy(rule("deny-b", 10, "deny", None, ZONE_B))
    decision = evaluate_access(p, ZONE_A, ZONE_B, SQL)
    assert not decision.allowed
    assert decision.matched_rule_id == "deny-b"
    assert decision.reason.startswith("Denied by rule 'deny-b'")


def test_lower_priority_number_wins():
    p = policy(
        rule("allow-ssh", 20, "allow", ZONE_A, ZONE_B, SSH),
        rule("deny-all-to-b", 50, "deny", None, ZONE_B),
    )
    assert evaluate_access(p, ZONE_A, ZONE_B, SSH).matched_rule_id == "allow-ssh"
    assert evaluate_access(p, ZONE_A, ZONE_B, SQL).matched_rule_id == "deny-all-to-b"


def test_priority_beats_definition_order():
    p = policy(
        rule("allow-late", 90, "allow", ZONE_A, ZONE_B),
        rule("deny-early", 5, "deny", ZONE_A, ZONE_B),
    )
    assert evaluate_access(p, ZONE_A, ZONE_B, SQL).matched_rule_id == "deny-early"


def test_deny_wins_a_priority_tie():
    p = policy(
        rule("a-allow", 10, "allow", ZONE_A, ZONE_B),
        rule("z-deny", 10, "deny", ZONE_A, ZONE_B),
    )
    decision = evaluate_access(p, ZONE_A, ZONE_B, SQL)
    assert not decision.allowed
    assert decision.matched_rule_id == "z-deny"


def test_equal_priority_and_action_ordered_by_id():
    p = policy(rule("rule-b", 10, "allow", None, None), rule("rule-a", 10, "allow", None, None))
    assert [r.id for r in evaluation_order(p)] == ["rule-a", "rule-b"]
    assert evaluate_access(p, ZONE_A, ZONE_B, SQL).matched_rule_id == "rule-a"


def test_wildcards_match_any_zone_and_protocol():
    p = policy(rule("allow-anything", 100, "allow", None, None))
    assert evaluate_access(p, "zone-x", "zone-y", Protocol.DNP3).allowed


def test_evaluation_is_deterministic_across_rule_orderings():
    rules = [
        rule("allow-1", 10, "allow", ZONE_A, None, SQL),
        rule("deny-1", 10, "deny", None, ZONE_B),
        rule("allow-2", 5, "allow", ZONE_A, ZONE_B, HTTPS),
    ]
    forward = evaluate_access(policy(*rules), ZONE_A, ZONE_B, SQL)
    backward = evaluate_access(policy(*reversed(rules)), ZONE_A, ZONE_B, SQL)
    assert forward == backward
    assert forward.matched_rule_id == "deny-1"
