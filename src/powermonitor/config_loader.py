"""Configuration file loader for powermonitor."""

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from loguru import logger

from .config import VALID_SUMMARY_MODES
from .config import PowerMonitorConfig
from .config import TUILayoutConfig

CONFIG_SECTION_KEYS = {
    "tui": {"interval", "stats_limit", "chart_limit", "layout"},
    "tui.layout": {
        "summary_mode",
        "live_weight",
        "stats_weight",
        "live_height",
        "stats_height",
        "summary_height",
        "chart_height",
        "panel_gap",
    },
    "database": {"path"},
    "cli": {"default_history_limit", "default_export_limit"},
    "logging": {"level"},
}


@dataclass(slots=True, frozen=True)
class ConfigValidationResult:
    """Result of strict config file validation."""

    path: Path
    errors: list[str]

    @property
    def is_valid(self) -> bool:
        """Return True when the config file has no validation errors."""
        return not self.errors


def get_config_path() -> Path:
    """Get path to user configuration file.

    Returns:
        Path to ~/.powermonitor/config.toml
    """
    return Path.home() / ".powermonitor" / "config.toml"


def layout_config_toml(layout: TUILayoutConfig) -> str:
    """Build the TOML table for TUI layout settings."""
    return f"""[tui.layout]
# Layout mode for live data and statistics: side_by_side or stacked
summary_mode = "{layout.summary_mode}"
# Relative widths when summary_mode = "side_by_side"
live_weight = {layout.live_weight}
stats_weight = {layout.stats_weight}
# Panel heights when summary_mode = "stacked"
live_height = {layout.live_height}
stats_height = {layout.stats_height}
# Shared summary row and chart sizing
summary_height = {layout.summary_height}
chart_height = {layout.chart_height}
# Gap between panels, in terminal cells
panel_gap = {layout.panel_gap}
"""


def default_config_toml(config: PowerMonitorConfig | None = None) -> str:
    """Build a commented default TOML config file."""
    config = config or PowerMonitorConfig()
    database_path = str(config.database_path).replace("\\", "\\\\").replace('"', '\\"')

    return f"""# powermonitor configuration file

[tui]
# Data collection interval in seconds
interval = {config.collection_interval}
# Number of readings for statistics
stats_limit = {config.stats_history_limit}
# Number of readings to display in chart
chart_limit = {config.chart_history_limit}

{layout_config_toml(config.layout)}

[database]
# Database file location
path = "{database_path}"

[cli]
# Default limit for history command
default_history_limit = {config.default_history_limit}
# Default limit for export command
default_export_limit = {config.default_export_limit}

[logging]
# Logging level: DEBUG, INFO, WARNING, ERROR
level = "{config.log_level}"
"""


def _convert_to_type(value: Any, target_type: type, field_name: str) -> Any:
    """Convert a value to the target type with descriptive error messages.

    Args:
        value: The value to convert
        target_type: The type to convert to (int, float, str, etc.)
        field_name: Dotted field name for error messages (e.g., 'tui.interval')

    Returns:
        Converted value

    Raises:
        ValueError: If conversion fails
    """
    try:
        return target_type(value)
    except (TypeError, ValueError):
        type_name = target_type.__name__
        if target_type is float:
            type_name = "a number"
        elif target_type is int:
            type_name = "an integer"
        raise ValueError(f"Invalid '{field_name}' value {value!r}; expected {type_name}") from None


def _get_nested_value(config: dict[str, Any], key_path: str, default: Any) -> Any:
    """Get a value from nested dict using dot notation.

    Args:
        config: The configuration dictionary
        key_path: Dot-separated path (e.g., 'tui.interval')
        default: Default value if path doesn't exist

    Returns:
        Value at the path or default
    """
    parts = key_path.split(".")
    current = config

    for part in parts:
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]

    return current


def _table_name(line: str) -> str | None:
    """Return a TOML table name from a line, or None when it is not a table header."""
    stripped = line.strip()
    if stripped.startswith("[[") or stripped.endswith("]]"):
        return None
    if not stripped.startswith("["):
        return None

    closing_index = stripped.find("]")
    if closing_index == -1:
        return None

    remainder = stripped[closing_index + 1 :].strip()
    if remainder and not remainder.startswith("#"):
        return None

    return stripped[1:closing_index].strip()


def _replace_or_insert_table(text: str, table_name: str, table_text: str, after_table: str | None = None) -> str:
    """Replace a TOML table, or insert it after another table when missing."""
    lines = text.splitlines()
    table_lines = table_text.rstrip("\n").splitlines()

    for index, line in enumerate(lines):
        if _table_name(line) != table_name:
            continue

        end_index = len(lines)
        for next_index in range(index + 1, len(lines)):
            if _table_name(lines[next_index]) is not None:
                end_index = next_index
                break

        updated_lines = [*lines[:index], *table_lines, "", *lines[end_index:]]
        return "\n".join(updated_lines).rstrip() + "\n"

    if after_table is not None:
        for index, line in enumerate(lines):
            if _table_name(line) != after_table:
                continue

            insert_index = len(lines)
            for next_index in range(index + 1, len(lines)):
                if _table_name(lines[next_index]) is not None:
                    insert_index = next_index
                    break

            updated_lines = [*lines[:insert_index], "", *table_lines, *lines[insert_index:]]
            return "\n".join(updated_lines).rstrip() + "\n"

    separator = "\n\n" if text.strip() else ""
    return f"{text.rstrip()}{separator}{table_text.rstrip()}\n"


def _warn_unknown_keys(user_config: dict[str, Any], section: str, valid_keys: set[str], config_path: Path) -> None:
    """Warn about unknown keys in a TOML section.

    Args:
        user_config: User configuration dictionary
        section: Section name (e.g., 'tui')
        valid_keys: Set of valid key names for this section
        config_path: Path to config file for error messages
    """
    section_data = _get_nested_value(user_config, section, None)
    if section_data is None:
        return

    if not isinstance(section_data, dict):
        return

    for key in section_data:
        if key not in valid_keys:
            logger.warning(
                f"Unknown key '{key}' in [{section}] section of {config_path} - ignoring "
                f"(valid keys: {', '.join(sorted(valid_keys))})"
            )


def _find_unknown_key_issues(user_config: dict[str, Any], config_path: Path) -> list[str]:
    """Find unknown keys in known config sections."""
    issues: list[str] = []

    for section, valid_keys in CONFIG_SECTION_KEYS.items():
        section_data = _get_nested_value(user_config, section, None)
        if section_data is None:
            continue

        if not isinstance(section_data, dict):
            continue

        for key in section_data:
            if key not in valid_keys:
                issues.append(
                    f"Unknown key '{key}' in [{section}] section of {config_path} - ignoring "
                    f"(valid keys: {', '.join(sorted(valid_keys))})"
                )

    return issues


def _find_top_level_section_issues(user_config: dict[str, Any], config_path: Path) -> list[str]:
    """Find unknown top-level config sections."""
    issues: list[str] = []

    for section in user_config:
        if section not in {"tui", "database", "cli", "logging"}:
            issues.append(f"Unknown config section [{section}] in {config_path} - ignoring")

    return issues


def _find_malformed_section_issues(user_config: dict[str, Any], config_path: Path) -> list[str]:
    """Find known sections that are not TOML tables."""
    issues: list[str] = []

    for section in {"tui", "database", "cli", "logging"}:
        if section in user_config and not isinstance(user_config[section], dict):
            issues.append(
                f"Config section [{section}] in {config_path} must be a table, "
                f"but got {type(user_config[section]).__name__} - ignoring section"
            )

    tui_layout = _get_nested_value(user_config, "tui.layout", None)
    if tui_layout is not None and not isinstance(tui_layout, dict):
        issues.append(
            f"Config section [tui.layout] in {config_path} must be a table, "
            f"but got {type(tui_layout).__name__} - ignoring section"
        )

    return issues


def _find_structure_issues(user_config: dict[str, Any], config_path: Path) -> list[str]:
    """Find unknown sections, unknown keys, and malformed section tables."""
    return [
        *_find_unknown_key_issues(user_config, config_path),
        *_find_top_level_section_issues(user_config, config_path),
        *_find_malformed_section_issues(user_config, config_path),
    ]


def _layout_error_message(field_name: str, value: Any) -> str | None:
    """Return a validation error for a layout value, or None when valid."""
    if field_name == "summary_mode":
        if not isinstance(value, str):
            return f"Invalid 'tui.layout.summary_mode' value {value!r}; expected a string"
        if value not in VALID_SUMMARY_MODES:
            valid_modes = ", ".join(sorted(VALID_SUMMARY_MODES))
            return f"summary_mode must be one of {valid_modes}, got {value}"
        return None

    if field_name == "panel_gap":
        if not isinstance(value, int) or value < 0:
            return f"panel_gap must be zero or positive, got {value}"
        return None

    if not isinstance(value, int) or value <= 0:
        return f"{field_name} must be positive, got {value}"
    return None


def _build_layout_config(
    user_config: dict[str, Any],
    default_layout: TUILayoutConfig,
    errors: list[str] | None = None,
) -> TUILayoutConfig:
    """Build TUILayoutConfig with per-field fallback, optionally collecting strict errors."""
    layout_values: dict[str, Any] = {
        "summary_mode": default_layout.summary_mode,
        "live_weight": default_layout.live_weight,
        "stats_weight": default_layout.stats_weight,
        "live_height": default_layout.live_height,
        "stats_height": default_layout.stats_height,
        "summary_height": default_layout.summary_height,
        "chart_height": default_layout.chart_height,
        "panel_gap": default_layout.panel_gap,
    }

    def report(message: str) -> None:
        if errors is None:
            logger.warning(f"{message} - using default layout value")
        else:
            errors.append(message)

    summary_mode_raw = _get_nested_value(user_config, "tui.layout.summary_mode", default_layout.summary_mode)
    if summary_mode_raw is not default_layout.summary_mode:
        message = _layout_error_message("summary_mode", summary_mode_raw)
        if message is None:
            layout_values["summary_mode"] = summary_mode_raw
        else:
            report(message)

    numeric_fields = (
        "live_weight",
        "stats_weight",
        "live_height",
        "stats_height",
        "summary_height",
        "chart_height",
        "panel_gap",
    )
    for field_name in numeric_fields:
        default_value = getattr(default_layout, field_name)
        raw_value = _get_nested_value(user_config, f"tui.layout.{field_name}", default_value)
        if raw_value is default_value:
            continue
        try:
            converted_value = _convert_to_type(raw_value, int, f"tui.layout.{field_name}")
        except ValueError as e:
            report(str(e))
            continue

        message = _layout_error_message(field_name, converted_value)
        if message is None:
            layout_values[field_name] = converted_value
        else:
            report(message)

    return TUILayoutConfig(**layout_values)


def _load_toml_file(config_path: Path) -> dict[str, Any] | None:
    """Load and parse TOML file, returning None on any error.

    Args:
        config_path: Path to TOML file

    Returns:
        Parsed TOML dict or None on error
    """
    try:
        with open(config_path, "rb") as f:
            return tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        logger.warning(f"Failed to parse TOML config from {config_path}: {e}")
        return None
    except OSError as e:
        logger.warning(f"Failed to read config file {config_path}: {e}")
        return None


def save_layout_config(layout: TUILayoutConfig, config_path: Path | None = None) -> Path:
    """Persist layout settings to the user config file.

    Existing config files are updated by replacing only the [tui.layout] table.
    If no config file exists, a full default config is created with the supplied
    layout values.
    """
    resolved_path = config_path or get_config_path()
    resolved_path.parent.mkdir(parents=True, exist_ok=True)

    if resolved_path.exists():
        current_text = resolved_path.read_text(encoding="utf-8")
        next_text = _replace_or_insert_table(
            current_text,
            table_name="tui.layout",
            table_text=layout_config_toml(layout),
            after_table="tui",
        )
    else:
        next_text = default_config_toml(PowerMonitorConfig(layout=layout))

    resolved_path.write_text(next_text, encoding="utf-8")
    validation = validate_config_file(resolved_path)
    if not validation.is_valid:
        error_text = "; ".join(validation.errors)
        raise ValueError(f"Saved layout config is invalid: {error_text}")
    return resolved_path


def _validate_config_structure(user_config: dict[str, Any], config_path: Path) -> None:
    """Validate TOML structure and warn about unknown sections/keys.

    Args:
        user_config: Loaded TOML configuration
        config_path: Path to config file for error messages
    """
    for issue in _find_structure_issues(user_config, config_path):
        logger.warning(issue)


def validate_config_file(config_path: Path | None = None) -> ConfigValidationResult:
    """Strictly validate a powermonitor config file.

    Runtime loading remains forgiving and falls back per field. This validator
    reports the same schema issues as errors so users can fix their config file
    before starting the TUI.
    """
    resolved_path = config_path or get_config_path()
    errors: list[str] = []

    if not resolved_path.exists():
        return ConfigValidationResult(
            path=resolved_path,
            errors=[f"Config file does not exist: {resolved_path}"],
        )

    try:
        with open(resolved_path, "rb") as f:
            user_config = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        return ConfigValidationResult(
            path=resolved_path,
            errors=[f"Failed to parse TOML config from {resolved_path}: {e}"],
        )
    except OSError as e:
        return ConfigValidationResult(
            path=resolved_path,
            errors=[f"Failed to read config file {resolved_path}: {e}"],
        )

    errors.extend(_find_structure_issues(user_config, resolved_path))

    default_config = PowerMonitorConfig()

    def convert_value(key_path: str, target_type: type, default: Any) -> Any:
        raw_value = _get_nested_value(user_config, key_path, default)
        if raw_value is default:
            return default
        try:
            return _convert_to_type(raw_value, target_type, key_path)
        except ValueError as e:
            errors.append(str(e))
            return default

    collection_interval = convert_value("tui.interval", float, default_config.collection_interval)
    stats_history_limit = convert_value("tui.stats_limit", int, default_config.stats_history_limit)
    chart_history_limit = convert_value("tui.chart_limit", int, default_config.chart_history_limit)
    default_history_limit = convert_value("cli.default_history_limit", int, default_config.default_history_limit)
    default_export_limit = convert_value("cli.default_export_limit", int, default_config.default_export_limit)
    layout = _build_layout_config(user_config, default_config.layout, errors)

    database_path_raw = _get_nested_value(user_config, "database.path", default_config.database_path)
    if not isinstance(database_path_raw, (str, Path)):
        errors.append(f"Invalid 'database.path' value {database_path_raw!r}; expected a string or Path")
        database_path = default_config.database_path
    else:
        database_path = database_path_raw

    log_level_raw = _get_nested_value(user_config, "logging.level", default_config.log_level)
    if not isinstance(log_level_raw, str):
        errors.append(f"Invalid 'logging.level' value {log_level_raw!r}; expected a string")
        log_level = default_config.log_level
    else:
        log_level = log_level_raw

    try:
        PowerMonitorConfig(
            collection_interval=collection_interval,
            stats_history_limit=stats_history_limit,
            chart_history_limit=chart_history_limit,
            database_path=database_path,
            default_history_limit=default_history_limit,
            default_export_limit=default_export_limit,
            log_level=log_level,
            layout=layout,
        )
    except ValueError as e:
        errors.append(str(e))

    return ConfigValidationResult(path=resolved_path, errors=errors)


def load_config() -> PowerMonitorConfig:
    """Load configuration from TOML file or use defaults.

    Priority: Config file > Defaults
    (CLI arguments will override in cli.py)

    Uses field-level fallback: if a single field is invalid, only that field
    falls back to default (other valid fields are preserved).

    Returns:
        PowerMonitorConfig with merged settings

    Examples:
        # Without config file - uses defaults
        config = load_config()

        # With config file - merges with defaults
        config = load_config()
        # CLI can then override: config.collection_interval = 2.0
    """
    config_path = get_config_path()

    # Get default values from PowerMonitorConfig (single source of truth)
    default_config = PowerMonitorConfig()

    # If config file doesn't exist, return defaults
    if not config_path.exists():
        return default_config

    # Load TOML file
    user_config = _load_toml_file(config_path)
    if user_config is None:
        logger.warning("Using default configuration")
        return default_config

    # Validate structure and warn about issues
    _validate_config_structure(user_config, config_path)

    # Extract values with field-level fallback to defaults
    # If a field conversion fails, we use the default for that field only
    def safe_convert(key_path: str, target_type: type, default: Any) -> Any:
        """Get and convert a config value, falling back to default on error."""
        raw_value = _get_nested_value(user_config, key_path, default)
        if raw_value is default:
            return default
        try:
            return _convert_to_type(raw_value, target_type, key_path)
        except ValueError as e:
            logger.warning(f"{e} - using default value {default!r}")
            return default

    collection_interval = safe_convert("tui.interval", float, default_config.collection_interval)
    stats_history_limit = safe_convert("tui.stats_limit", int, default_config.stats_history_limit)
    chart_history_limit = safe_convert("tui.chart_limit", int, default_config.chart_history_limit)
    default_history_limit = safe_convert("cli.default_history_limit", int, default_config.default_history_limit)
    default_export_limit = safe_convert("cli.default_export_limit", int, default_config.default_export_limit)
    layout = _build_layout_config(user_config, default_config.layout)

    # Database path (ensure it's a string or Path; expanduser happens in __post_init__)
    database_path_raw = _get_nested_value(user_config, "database.path", default_config.database_path)
    if not isinstance(database_path_raw, (str, Path)):
        logger.warning(
            f"Invalid 'database.path' value {database_path_raw!r}; expected a string or Path - "
            f"using default value {default_config.database_path!r}"
        )
        database_path = default_config.database_path
    else:
        database_path = database_path_raw

    # Log level (ensure it's a string, validation happens in __post_init__)
    log_level_raw = _get_nested_value(user_config, "logging.level", default_config.log_level)
    if not isinstance(log_level_raw, str):
        logger.warning(
            f"Invalid 'logging.level' value {log_level_raw!r}; expected a string - "
            f"using default value {default_config.log_level!r}"
        )
        log_level = default_config.log_level
    else:
        log_level = log_level_raw

    # Create PowerMonitorConfig instance (validation happens in __post_init__)
    try:
        return PowerMonitorConfig(
            collection_interval=collection_interval,
            stats_history_limit=stats_history_limit,
            chart_history_limit=chart_history_limit,
            database_path=database_path,
            default_history_limit=default_history_limit,
            default_export_limit=default_export_limit,
            log_level=log_level,
            layout=layout,
        )
    except ValueError as e:
        # This should rarely happen now (only if __post_init__ validation fails)
        logger.error(f"Invalid configuration values: {e}")
        logger.warning("Falling back to safe default configuration")
        return PowerMonitorConfig()  # Use all defaults
