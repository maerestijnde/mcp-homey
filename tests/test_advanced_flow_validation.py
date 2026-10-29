import copy

import pytest

from homey_mcp.client.flows import validate_advanced_flow

T, A, C, D = (
    "11111111-1111-4111-8111-111111111111",
    "22222222-2222-4222-8222-222222222222",
    "33333333-3333-4333-8333-333333333333",
    "44444444-4444-4444-8444-444444444444",
)

CATALOG = {
    "homey:manager:logic:webhook": {"trigger": {"args": [{"name": "event", "type": "text"}]}},
    "homey:manager:notifications:create_notification": {"action": {"args": [{"name": "text", "type": "text"}]}},
    "homey:manager:logic:lt": {"condition": {"args": [{"name": "value", "type": "number", "required": False}]}},
    "homey:app:com.athom.homeyscript:runCode_v2": {
        "condition": {"args": [{"name": "code", "type": "code"}]},
        "action": {"args": [{"name": "code", "type": "code"}]},
    },
}

VALID = {
    "name": "Test",
    "enabled": False,
    "cards": {
        T: {"type": "trigger", "id": "homey:manager:logic:webhook", "args": {"event": "x"}, "x": 0, "y": 0, "outputSuccess": [C]},
        C: {"type": "condition", "id": "homey:manager:logic:lt", "x": 400, "y": 0, "outputTrue": [D]},
        D: {"type": "delay", "args": {"delay": {"number": "5", "multiplier": 1}}, "x": 800, "y": 0, "outputSuccess": [A]},
        A: {"type": "action", "id": "homey:manager:notifications:create_notification", "args": {"text": "hi"}, "x": 1200, "y": 0},
    },
}


def broken(mutate):
    flow = copy.deepcopy(VALID)
    mutate(flow)
    return validate_advanced_flow(flow, CATALOG)


def test_valid_flow_passes():
    assert validate_advanced_flow(VALID, CATALOG) == []


@pytest.mark.parametrize(
    "mutate, expected",
    [
        (lambda f: f.update(name=None), "name"),
        (lambda f: f.update(name='"null"'), "name"),
        (lambda f: f.update(cards={}), "cards must be"),
        (lambda f: f["cards"].update({"card1": f["cards"].pop(A)}), "key must be a UUID"),
        (lambda f: f["cards"][T].update(id="motion_sensor"), "no trigger card"),
        (lambda f: f["cards"][A].update(type="condition"), "is a action card"),
        (lambda f: f["cards"][A].pop("args"), "missing required arg 'text'"),
        (lambda f: f["cards"][A].pop("x"), "x and y"),
        (lambda f: f["cards"][T].update(outputSuccess=["99999999-9999-4999-8999-999999999999"]), "unknown card"),
        (lambda f: f["cards"][D]["args"]["delay"].update(multiplier=5), "delay needs"),
        (lambda f: f["cards"][T].update(type="start", id=None), None),
        (lambda f: f["cards"].pop(T), "at least one trigger"),
        (lambda f: f["cards"].update({"55555555-5555-4555-8555-555555555555": {"type": "any", "x": 0, "y": 0, "input": [f"{C}::outputMaybe"]}}), "input"),
    ],
)
def test_broken_flows_are_rejected(mutate, expected):
    errors = broken(mutate)
    if expected is None:
        assert errors == []  # start card replaces trigger: still valid
    else:
        assert any(expected in e for e in errors), errors


@pytest.mark.parametrize("kind", ["condition", "action"])
def test_id_shared_by_condition_and_action(kind):
    flow = copy.deepcopy(VALID)
    flow["cards"][C].update(type=kind, id="homey:app:com.athom.homeyscript:runCode_v2", args={"code": "return true"})
    assert validate_advanced_flow(flow, CATALOG) == []


def test_optional_arg_may_be_omitted():
    assert not any("'value'" in e for e in validate_advanced_flow(VALID, CATALOG))
