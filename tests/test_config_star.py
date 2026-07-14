"""Tests for STAR config additions."""

import importlib


def test_scout_model_vars_exist():
    import config
    importlib.reload(config)
    assert hasattr(config, "MODEL_SCOUT_AUDIENCE")
    assert hasattr(config, "MODEL_SCOUT_TREND")
    assert hasattr(config, "MODEL_SCOUT_DISCOVERY")
    assert hasattr(config, "MODEL_SCOUT_FIT")
    assert all(isinstance(getattr(config, v), str) for v in [
        "MODEL_SCOUT_AUDIENCE", "MODEL_SCOUT_TREND", "MODEL_SCOUT_DISCOVERY", "MODEL_SCOUT_FIT"
    ])


def test_target_model_vars_exist():
    import config
    importlib.reload(config)
    for v in ["MODEL_TARGET_COMPETITOR", "MODEL_TARGET_PLANNER", "MODEL_TARGET_BRIEF", "MODEL_TARGET_BUDGET"]:
        assert hasattr(config, v)
        assert isinstance(getattr(config, v), str)


def test_activate_model_vars_exist():
    import config
    importlib.reload(config)
    for v in ["MODEL_ACTIVATE_OUTREACH", "MODEL_ACTIVATE_AUDITOR", "MODEL_ACTIVATE_CONTRACT", "MODEL_ACTIVATE_AMPLIFIER"]:
        assert hasattr(config, v)
        assert isinstance(getattr(config, v), str)


def test_report_model_vars_exist():
    import config
    importlib.reload(config)
    for v in ["MODEL_REPORT_LANDING", "MODEL_REPORT_PERFORMANCE", "MODEL_REPORT_ROI", "MODEL_REPORT_GENERATOR"]:
        assert hasattr(config, v)
        assert isinstance(getattr(config, v), str)


def test_protocol_model_var_exists():
    import config
    importlib.reload(config)
    assert hasattr(config, "MODEL_PROTOCOL_REGISTRY")
    assert isinstance(config.MODEL_PROTOCOL_REGISTRY, str)


def test_connector_timeout_exists():
    import config
    importlib.reload(config)
    assert hasattr(config, "CONNECTOR_TIMEOUT_SECONDS")
    assert isinstance(config.CONNECTOR_TIMEOUT_SECONDS, int)
    assert config.CONNECTOR_TIMEOUT_SECONDS > 0