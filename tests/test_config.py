"""Tests for PowerMonitorConfig."""

import warnings
from typing import Any
from typing import cast

import pytest

from powermonitor.config import PowerMonitorConfig
from powermonitor.config import TUILayoutConfig


def test_config_default_values():
    """Test PowerMonitorConfig with default values."""
    config = PowerMonitorConfig()

    assert config.collection_interval == 1.0
    assert config.stats_history_limit == 100
    assert config.chart_history_limit == 60
    assert config.layout == TUILayoutConfig()


def test_config_custom_values():
    """Test PowerMonitorConfig with custom values."""
    config = PowerMonitorConfig(
        collection_interval=2.5,
        stats_history_limit=200,
        chart_history_limit=120,
    )

    assert config.collection_interval == 2.5
    assert config.stats_history_limit == 200
    assert config.chart_history_limit == 120


def test_layout_config_default_values():
    """Test TUILayoutConfig with default values."""
    layout = TUILayoutConfig()

    assert layout.summary_mode == "side_by_side"
    assert layout.live_weight == 1
    assert layout.stats_weight == 1
    assert layout.live_height == 8
    assert layout.stats_height == 10
    assert layout.summary_height == 10
    assert layout.chart_height == 20
    assert layout.panel_gap == 1


def test_layout_config_custom_values():
    """Test TUILayoutConfig with custom values."""
    layout = TUILayoutConfig(
        summary_mode="stacked",
        live_weight=2,
        stats_weight=3,
        live_height=7,
        stats_height=9,
        summary_height=11,
        chart_height=15,
        panel_gap=0,
    )

    assert layout.summary_mode == "stacked"
    assert layout.live_weight == 2
    assert layout.stats_weight == 3
    assert layout.live_height == 7
    assert layout.stats_height == 9
    assert layout.summary_height == 11
    assert layout.chart_height == 15
    assert layout.panel_gap == 0


def test_layout_config_invalid_summary_mode():
    """Test that invalid summary_mode raises ValueError."""
    with pytest.raises(ValueError, match="summary_mode must be one of"):
        TUILayoutConfig(summary_mode=cast(Any, "grid"))


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("live_weight", 0),
        ("stats_weight", -1),
        ("live_height", 0),
        ("stats_height", -1),
        ("summary_height", 0),
        ("chart_height", -1),
    ],
)
def test_layout_config_positive_fields(field_name, value):
    """Test that layout size and weight fields must be positive."""
    with pytest.raises(ValueError, match=f"{field_name} must be positive"):
        TUILayoutConfig(**{field_name: value})


def test_layout_config_panel_gap_allows_zero():
    """Test that panel_gap may be zero."""
    layout = TUILayoutConfig(panel_gap=0)

    assert layout.panel_gap == 0


def test_layout_config_negative_panel_gap():
    """Test that negative panel_gap raises ValueError."""
    with pytest.raises(ValueError, match="panel_gap must be zero or positive"):
        TUILayoutConfig(panel_gap=-1)


def test_config_negative_collection_interval():
    """Test that negative collection_interval raises ValueError."""
    with pytest.raises(ValueError, match="collection_interval must be positive"):
        PowerMonitorConfig(collection_interval=-1.0)


def test_config_zero_collection_interval():
    """Test that zero collection_interval raises ValueError."""
    with pytest.raises(ValueError, match="collection_interval must be positive"):
        PowerMonitorConfig(collection_interval=0.0)


def test_config_negative_stats_limit():
    """Test that negative stats_history_limit raises ValueError."""
    with pytest.raises(ValueError, match="stats_history_limit must be positive"):
        PowerMonitorConfig(stats_history_limit=-10)


def test_config_zero_stats_limit():
    """Test that zero stats_history_limit raises ValueError."""
    with pytest.raises(ValueError, match="stats_history_limit must be positive"):
        PowerMonitorConfig(stats_history_limit=0)


def test_config_negative_chart_limit():
    """Test that negative chart_history_limit raises ValueError."""
    with pytest.raises(ValueError, match="chart_history_limit must be positive"):
        PowerMonitorConfig(chart_history_limit=-5)


def test_config_zero_chart_limit():
    """Test that zero chart_history_limit raises ValueError."""
    with pytest.raises(ValueError, match="chart_history_limit must be positive"):
        PowerMonitorConfig(chart_history_limit=0)


def test_config_very_short_interval_warning():
    """Test that very short interval triggers a warning."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        config = PowerMonitorConfig(collection_interval=0.05)

        # Check that a warning was issued
        assert len(w) == 1
        assert issubclass(w[0].category, UserWarning)
        assert "high CPU usage" in str(w[0].message)
        assert "0.05" in str(w[0].message)

        # Config should still be created successfully
        assert config.collection_interval == 0.05


def test_config_minimum_safe_interval_no_warning():
    """Test that 0.1s interval does not trigger warning."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        config = PowerMonitorConfig(collection_interval=0.1)

        # No warning should be issued at exactly 0.1s
        assert len(w) == 0
        assert config.collection_interval == 0.1


def test_config_normal_interval_no_warning():
    """Test that normal intervals don't trigger warnings."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        config = PowerMonitorConfig(collection_interval=1.0)

        assert len(w) == 0
        assert config.collection_interval == 1.0
