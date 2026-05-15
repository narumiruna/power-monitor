# powermonitor Improvement Plan

## Goal

Make powermonitor easier to configure, inspect, and operate without changing the existing data collection behavior.
The first completed outcome is a tested `powermonitor config` command group plus updated user documentation.

## Context

The application already has a TOML configuration loader in `src/powermonitor/config_loader.py`, a validated
`PowerMonitorConfig` dataclass in `src/powermonitor/config.py`, and Typer CLI commands in `src/powermonitor/cli.py`.
The missing piece is a user-facing way to create, inspect, and validate `~/.powermonitor/config.toml` without launching
the TUI.

## Non-Goals

- Do not change IOKit, SMC, or `ioreg` collection semantics in this plan.
- Do not migrate the SQLite schema or historical readings.
- Do not add dynamic TUI config reload or multiple config profiles in the first implementation slice.
- Do not add dependencies unless stdlib and existing Typer/Rich APIs cannot support the accepted behavior.

## Assumptions

- `powermonitor` should continue to launch the TUI when invoked without a subcommand.
- CLI arguments should continue to override config file values for the TUI.
- Config file creation should be conservative and should not overwrite an existing file unless an explicit flag is added.

## Unknowns

- Should `powermonitor config init` support `--force` overwrite behavior? Resolve before implementing `init`; verify with
  CLI tests for existing-file behavior.
- Should `powermonitor config show` output Rich text only, or also support machine-readable JSON? Resolve before changing
  output shape; verify with tests for the chosen format.
- Should `powermonitor config edit` be included in the first slice? Resolve by deciding whether launching `$EDITOR` is
  important enough to test and document now.

## Plan

- [ ] Capture the current quality baseline before implementation; verify with `make all` and record any pre-existing
  failures before changing code.
- [ ] Add a `config` Typer command group in `src/powermonitor/cli.py` that does not interfere with default TUI launch;
  verify with `uv run powermonitor --help` and existing CLI tests.
- [ ] Add `powermonitor config show` to display the effective configuration and config file path; verify with a CLI test
  that uses the existing `temp_config` fixture and asserts database path, interval, limits, and log level are shown.
- [ ] Add `powermonitor config init` to create a commented default config at `get_config_path()` when no file exists;
  verify with a CLI test using `monkeypatch` and `tmp_path` that the file is created and valid TOML.
- [ ] Define and test existing-file behavior for `config init`; verify that the command refuses to overwrite by default
  or that `--force` behavior is explicitly covered by CLI tests.
- [ ] Add `powermonitor config validate` to parse and validate the configured TOML without starting the TUI; verify with
  tests for valid TOML, invalid TOML syntax, invalid field values, unknown sections, and unknown keys.
- [ ] Reuse `PowerMonitorConfig` and `config_loader` validation paths instead of adding a second config schema; verify
  with focused tests in `tests/test_config_loader.py` or `tests/test_cli.py`.
- [ ] Update `README.md` with the new `powermonitor config` commands and examples; verify the documented commands match
  `uv run powermonitor config --help`.
- [ ] Decide whether `powermonitor config edit` belongs in this release slice; if accepted, implement it with a mocked
  editor invocation test, otherwise leave it as a later candidate in this file.
- [ ] Run the final quality gate; verify with `make all` and `uv build --no-sources`.

## Later Candidates

- [ ] Add data analysis documentation with CSV and JSON examples; verify by adding a README or docs section that uses
  fields produced by `powermonitor export`.
- [ ] Add a battery health interpretation guide; verify that thresholds match the `health` command behavior in
  `src/powermonitor/cli.py`.
- [ ] Investigate dynamic TUI config reload; verify feasibility with a small design note covering file watching,
  validation failures, and live widget update behavior before writing code.
- [ ] Investigate multiple config profiles; verify the design with examples for profile selection, default fallback, and
  backwards compatibility with `~/.powermonitor/config.toml`.

## Risks

- A `config` command group can accidentally break the no-argument TUI entry path if Typer wiring changes are not covered
  by tests.
- Config validation can diverge from runtime behavior if it duplicates schema logic instead of reusing
  `PowerMonitorConfig` and `load_config` internals.
- `config init` can destroy user settings if overwrite behavior is not explicit and tested.
- `config edit` can be brittle across shells and editors unless it is small, optional, and covered with mocks.

## Rollback / Recovery

- Revert the config command group and README changes if default `powermonitor` launch behavior regresses.
- If a release is already published with broken config commands, ship a patch release that disables the affected command
  path while keeping existing TUI, database, and collector behavior unchanged.

## Completion Checklist

- [ ] `powermonitor config show`, `powermonitor config init`, and `powermonitor config validate` are implemented and
  verified by CLI tests.
- [ ] Default `powermonitor` invocation still launches the TUI path, verified by existing or new CLI/TUI tests.
- [ ] Runtime config loading and config validation share the same schema behavior, verified by tests that cover invalid
  values and unknown keys.
- [ ] README usage examples match command help, verified with `uv run powermonitor config --help`.
- [ ] Repository quality gates pass, verified with `make all` and `uv build --no-sources`.
