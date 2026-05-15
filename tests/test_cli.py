"""Tests for CLI commands."""

import json
import re
import tomllib
from datetime import UTC
from datetime import datetime
from datetime import timedelta
from pathlib import Path

from typer.testing import CliRunner

from powermonitor import cli as cli_module
from powermonitor import config_loader
from powermonitor.cli import app
from powermonitor.config import PowerMonitorConfig
from powermonitor.database import Database
from powermonitor.models import PowerReading

runner = CliRunner()


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text.

    Args:
        text: Text with ANSI codes

    Returns:
        Text without ANSI codes
    """
    ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
    return ansi_escape.sub("", text)


def create_test_readings(database: Database, count: int = 10) -> list[PowerReading]:
    """Create test readings in database.

    Args:
        database: Database instance
        count: Number of readings to create

    Returns:
        List of created PowerReading objects
    """
    readings = []
    base_time = datetime.now(UTC)

    for i in range(count):
        reading = PowerReading(
            timestamp=base_time - timedelta(seconds=i * 60),  # 1 minute apart
            watts_actual=40.0 + i,
            watts_negotiated=67,
            voltage=20.0,
            amperage=2.0 + (i * 0.1),
            current_capacity=3500,
            max_capacity=4709,
            battery_percent=74,
            is_charging=True,
            external_connected=True,
            charger_name="USB-C Power Adapter" if i % 2 == 0 else None,
            charger_manufacturer="Apple Inc." if i % 2 == 0 else None,
        )
        database.insert_reading(reading)
        readings.append(reading)

    return readings


def patch_config_path(monkeypatch, config_path: Path) -> None:
    """Point CLI config commands at a test config path."""
    monkeypatch.setattr(config_loader, "get_config_path", lambda: config_path)


def test_default_invocation_launches_tui_with_cli_overrides(monkeypatch, temp_config):
    """Test that invoking powermonitor without a subcommand still launches the TUI path."""
    launched: dict[str, object] = {}

    class DummyPowerMonitorApp:
        def __init__(self, config: PowerMonitorConfig) -> None:
            launched["config"] = config

        def run(self) -> None:
            launched["ran"] = True

    monkeypatch.setattr(cli_module.sys, "platform", "darwin")
    monkeypatch.setattr(cli_module, "PowerMonitorApp", DummyPowerMonitorApp)

    result = runner.invoke(
        app,
        ["--interval", "2.5", "--stats-limit", "42", "--chart-limit", "24", "--debug"],
    )

    assert result.exit_code == 0
    assert launched["ran"] is True
    config = launched["config"]
    assert isinstance(config, PowerMonitorConfig)
    assert config.collection_interval == 2.5
    assert config.stats_history_limit == 42
    assert config.chart_history_limit == 24
    assert config.log_level == "DEBUG"


def test_config_show_displays_effective_config(temp_config, temp_db):
    """Test config show displays the effective loaded config."""
    result = runner.invoke(app, ["config", "show"])

    output = strip_ansi(result.stdout)
    assert result.exit_code == 0
    assert "Effective Configuration" in output
    assert str(temp_config) in output
    assert str(temp_db) in output
    assert "Collection interval" in output
    assert "1 seconds" in output
    assert "Stats history limit" in output
    assert "100" in output
    assert "Chart history limit" in output
    assert "60" in output
    assert "Layout mode" in output
    assert "side_by_side" in output
    assert "Chart height" in output
    assert "20" in output
    assert "Log level" in output
    assert "INFO" in output


def test_config_init_creates_default_config(monkeypatch, tmp_path):
    """Test config init creates a commented, valid default TOML file."""
    config_path = tmp_path / ".powermonitor" / "config.toml"
    patch_config_path(monkeypatch, config_path)

    result = runner.invoke(app, ["config", "init"])

    assert result.exit_code == 0
    assert "Created config file" in strip_ansi(result.stdout)
    assert config_path.exists()
    content = config_path.read_text(encoding="utf-8")
    assert "# powermonitor configuration file" in content
    parsed = tomllib.loads(content)
    assert parsed["tui"]["interval"] == 1.0
    assert parsed["tui"]["layout"]["summary_mode"] == "side_by_side"
    assert parsed["tui"]["layout"]["chart_height"] == 20
    assert parsed["database"]["path"]
    assert parsed["logging"]["level"] == "INFO"


def test_config_init_refuses_existing_config(monkeypatch, tmp_path):
    """Test config init does not overwrite an existing config file."""
    config_path = tmp_path / "config.toml"
    original = '[logging]\nlevel = "DEBUG"\n'
    config_path.write_text(original, encoding="utf-8")
    patch_config_path(monkeypatch, config_path)

    result = runner.invoke(app, ["config", "init"])

    assert result.exit_code == 1
    assert "already exists" in strip_ansi(result.stdout)
    assert config_path.read_text(encoding="utf-8") == original


def test_config_validate_valid_config(temp_config):
    """Test config validate succeeds for a valid config file."""
    result = runner.invoke(app, ["config", "validate"])

    assert result.exit_code == 0
    assert "Config file is valid" in strip_ansi(result.stdout)
    assert str(temp_config) in strip_ansi(result.stdout)


def test_config_validate_invalid_toml(monkeypatch, tmp_path):
    """Test config validate reports TOML syntax errors."""
    config_path = tmp_path / "config.toml"
    config_path.write_text("invalid toml", encoding="utf-8")
    patch_config_path(monkeypatch, config_path)

    result = runner.invoke(app, ["config", "validate"])

    assert result.exit_code == 1
    assert "Failed to parse TOML config" in strip_ansi(result.stdout)


def test_config_validate_invalid_field_value(monkeypatch, tmp_path):
    """Test config validate reports invalid field values."""
    config_path = tmp_path / "config.toml"
    config_path.write_text("[tui]\ninterval = 0\n", encoding="utf-8")
    patch_config_path(monkeypatch, config_path)

    result = runner.invoke(app, ["config", "validate"])

    assert result.exit_code == 1
    assert "collection_interval must be positive" in strip_ansi(result.stdout)


def test_config_validate_unknown_section(monkeypatch, tmp_path):
    """Test config validate reports unknown config sections."""
    config_path = tmp_path / "config.toml"
    config_path.write_text('[unknown]\nkey = "value"\n', encoding="utf-8")
    patch_config_path(monkeypatch, config_path)

    result = runner.invoke(app, ["config", "validate"])

    assert result.exit_code == 1
    assert "Unknown config section [unknown]" in strip_ansi(result.stdout)


def test_config_validate_unknown_key(monkeypatch, tmp_path):
    """Test config validate reports unknown keys in known sections."""
    config_path = tmp_path / "config.toml"
    config_path.write_text("[tui]\ninterval = 1.0\ntyop = true\n", encoding="utf-8")
    patch_config_path(monkeypatch, config_path)

    result = runner.invoke(app, ["config", "validate"])

    assert result.exit_code == 1
    assert "Unknown key 'tyop'" in strip_ansi(result.stdout)


def test_config_validate_invalid_layout(monkeypatch, tmp_path):
    """Test config validate reports invalid layout values."""
    config_path = tmp_path / "config.toml"
    config_path.write_text('[tui.layout]\nsummary_mode = "grid"\nlive_weight = 0\n', encoding="utf-8")
    patch_config_path(monkeypatch, config_path)

    result = runner.invoke(app, ["config", "validate"])

    assert result.exit_code == 1
    output = strip_ansi(result.stdout)
    assert "summary_mode must be one of" in output
    assert "live_weight must be positive" in output


def test_config_validate_unknown_layout_key(monkeypatch, tmp_path):
    """Test config validate reports unknown keys in layout section."""
    config_path = tmp_path / "config.toml"
    config_path.write_text("[tui.layout]\nunknown_key = true\n", encoding="utf-8")
    patch_config_path(monkeypatch, config_path)

    result = runner.invoke(app, ["config", "validate"])

    assert result.exit_code == 1
    assert "Unknown key 'unknown_key' in [tui.layout]" in strip_ansi(result.stdout)


def test_export_csv(database, temp_config, tmp_path):
    """Test exporting readings to CSV format."""
    # Create test data
    create_test_readings(database, count=5)

    # Export to CSV
    output_file = tmp_path / "test_export.csv"
    result = runner.invoke(
        app,
        ["export", str(output_file), "--limit", "5"],
    )

    assert result.exit_code == 0
    assert "Exported 5 readings" in strip_ansi(result.stdout)
    assert output_file.exists()

    # Verify CSV content
    content = output_file.read_text()
    lines = content.strip().split("\n")
    assert len(lines) == 6  # Header + 5 data rows
    assert lines[0].startswith("timestamp,watts_actual,watts_negotiated")


def test_export_json(database, temp_config, tmp_path):
    """Test exporting readings to JSON format."""
    # Create test data
    create_test_readings(database, count=3)

    # Export to JSON
    output_file = tmp_path / "test_export.json"
    result = runner.invoke(
        app,
        ["export", str(output_file), "--limit", "3"],
    )

    assert result.exit_code == 0
    assert "Exported 3 readings" in strip_ansi(result.stdout)
    assert output_file.exists()

    # Verify JSON content
    with output_file.open() as f:
        data = json.load(f)
    assert isinstance(data, list)
    assert len(data) == 3
    assert "timestamp" in data[0]
    assert "watts_actual" in data[0]


def test_export_auto_detect_format(database, temp_config, tmp_path):
    """Test export format auto-detection from file extension."""
    # Create test data
    create_test_readings(database, count=2)

    # Test CSV detection
    csv_file = tmp_path / "auto.csv"
    result = runner.invoke(
        app,
        ["export", str(csv_file)],
    )
    assert result.exit_code == 0
    assert csv_file.exists()

    # Test JSON detection
    json_file = tmp_path / "auto.json"
    result = runner.invoke(
        app,
        ["export", str(json_file)],
    )
    assert result.exit_code == 0
    assert json_file.exists()


def test_export_invalid_format(temp_config, tmp_path):
    """Test export with invalid format."""
    output_file = tmp_path / "test.txt"
    result = runner.invoke(
        app,
        ["export", str(output_file)],
    )
    assert result.exit_code == 1
    assert "Cannot detect format" in result.stdout


def test_export_no_readings(database, temp_config, tmp_path):
    """Test export with empty database."""
    output_file = tmp_path / "empty.csv"
    result = runner.invoke(
        app,
        ["export", str(output_file)],
    )
    assert result.exit_code == 0
    assert "No readings found" in result.stdout


def test_export_with_limit(database, temp_config, tmp_path):
    """Test export with limit parameter."""
    # Create 10 readings
    create_test_readings(database, count=10)

    # Export only 3
    output_file = tmp_path / "limited.csv"
    result = runner.invoke(
        app,
        ["export", str(output_file), "--limit", "3"],
    )
    assert result.exit_code == 0
    assert "Exported 3 readings" in strip_ansi(result.stdout)


def test_stats_command(database, temp_config):
    """Test stats command."""
    # Create test data
    create_test_readings(database, count=5)

    result = runner.invoke(
        app,
        ["stats"],
    )
    assert result.exit_code == 0
    assert "Database Statistics" in result.stdout
    assert "Total readings" in result.stdout
    assert "5" in result.stdout


def test_stats_empty_database(database, temp_config):
    """Test stats command with empty database."""
    result = runner.invoke(
        app,
        ["stats"],
    )
    assert result.exit_code == 0
    assert "No readings in database" in result.stdout


def test_cleanup_with_days(database, temp_config):
    """Test cleanup command with --days parameter."""
    # Create readings with different timestamps
    base_time = datetime.now(UTC)
    for i in range(5):
        reading = PowerReading(
            timestamp=base_time - timedelta(days=i * 10),  # 0, 10, 20, 30, 40 days old
            watts_actual=40.0,
            watts_negotiated=67,
            voltage=20.0,
            amperage=2.0,
            current_capacity=3500,
            max_capacity=4709,
            battery_percent=74,
            is_charging=True,
            external_connected=True,
            charger_name=None,
            charger_manufacturer=None,
        )
        database.insert_reading(reading)

    # Delete readings older than 25 days (should delete 2)
    result = runner.invoke(
        app,
        ["cleanup", "--days", "25"],
    )
    assert result.exit_code == 0
    assert "Deleted 2 old readings" in strip_ansi(result.stdout)

    # Verify remaining readings
    remaining = database.query_history(limit=None)
    assert len(remaining) == 3


def test_cleanup_all_with_confirmation(database, temp_config):
    """Test cleanup --all with user confirmation."""
    # Create test data
    create_test_readings(database, count=5)

    # Confirm deletion
    result = runner.invoke(
        app,
        ["cleanup", "--all"],
        input="y\n",
    )
    assert result.exit_code == 0
    assert "Deleted all 5 readings" in strip_ansi(result.stdout)

    # Verify database is empty
    remaining = database.query_history(limit=None)
    assert len(remaining) == 0


def test_cleanup_all_cancelled(database, temp_config):
    """Test cleanup --all when user cancels."""
    # Create test data
    create_test_readings(database, count=3)

    # Cancel deletion
    result = runner.invoke(
        app,
        ["cleanup", "--all"],
        input="n\n",
    )
    assert result.exit_code == 0
    assert "Operation cancelled" in result.stdout

    # Verify data still exists
    remaining = database.query_history(limit=None)
    assert len(remaining) == 3


def test_cleanup_missing_parameters(temp_config):
    """Test cleanup command with missing parameters."""
    result = runner.invoke(
        app,
        ["cleanup"],
    )
    assert result.exit_code == 1
    assert "Must specify either --days N or --all" in result.stdout


def test_history_command(database, temp_config):
    """Test history command."""
    # Create test data
    create_test_readings(database, count=5)

    result = runner.invoke(
        app,
        ["history", "--limit", "5"],
    )
    assert result.exit_code == 0
    assert "Recent Power Readings" in result.stdout
    assert "Time" in result.stdout
    assert "Power" in result.stdout


def test_history_empty_database(database, temp_config):
    """Test history command with empty database."""
    result = runner.invoke(
        app,
        ["history"],
    )
    assert result.exit_code == 0
    assert "No readings in database" in result.stdout


def test_health_command(database, temp_config):
    """Test health command."""
    # Create readings over multiple days
    base_time = datetime.now(UTC)
    for day in range(7):
        for i in range(5):  # 5 readings per day
            reading = PowerReading(
                timestamp=base_time - timedelta(days=day, hours=i),
                watts_actual=40.0,
                watts_negotiated=67,
                voltage=20.0,
                amperage=2.0,
                current_capacity=3500,
                max_capacity=4700 - day,  # Simulate slight degradation
                battery_percent=74,
                is_charging=True,
                external_connected=True,
                charger_name=None,
                charger_manufacturer=None,
            )
            database.insert_reading(reading)

    result = runner.invoke(
        app,
        ["health", "--days", "7"],
    )
    assert result.exit_code == 0
    assert "Battery Health Analysis" in result.stdout
    assert "mAh" in result.stdout


def test_health_no_data(database, temp_config):
    """Test health command with no data."""
    result = runner.invoke(
        app,
        ["health", "--days", "7"],
    )
    assert result.exit_code == 0
    assert "No readings found" in result.stdout
