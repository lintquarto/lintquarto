"""Merge arguments from command line interface (CLI) and configuration file."""

import argparse

from lintquarto.config import LintquartoConfig

# =============================================================================
# Main function: merge configuration file with parsed CLI arguments.
# =============================================================================


def merge_config(
    args: argparse.Namespace,
    config: LintquartoConfig,
    *,
    verbose: bool = False,
) -> argparse.Namespace:
    """
    Merge `[tool.lintquarto]` config into parsed CLI args.

    CLI flags always win for list arguments; config values are used only when
    the corresponding CLI argument was not supplied. Boolean flags use OR
    semantics: `True` from either source wins.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed command-line arguments.
    config : LintquartoConfig
        Settings loaded from `pyproject.toml`.
    verbose : bool, optional
        If `True`, print a message for each value that is set or overridden.
        Defaults to `False`.

    Returns
    -------
    argparse.Namespace
        Updated namespace with config values back-filled where CLI was silent.
    """
    # No configuration file with [tool.lintquarto] was found
    if config.config_path is None:
        if verbose:
            print("Configuration: no [tool.lintquarto] section found.")
        return args

    # Found configuration file with [tool.lintquarto] section
    if verbose:
        print(
            f"Configuration: reading [tool.lintquarto] from "
            f"{config.config_path}"
        )

    # Primary targets
    for arg_name in ("linters", "paths"):
        _merge_prefer_cli(
            args,
            config,
            arg_name=arg_name,
            verbose=verbose,
        )

    # Behaviour modifications
    for arg_name in ("exclude", "custom_commands"):
        _merge_additive(
            args,
            config,
            arg_name=arg_name,
            verbose=verbose,
        )
    for flag in ("lint_non_exec", "verbose", "keep_temp"):
        _merge_bool_or(
            args,
            config,
            flag=flag,
            verbose=verbose,
        )

    return args


# =============================================================================
# Helpers: Different merge preferences (prefer CLI, additive, or boolean)
# =============================================================================


def _merge_prefer_cli(
    args: argparse.Namespace,
    config: LintquartoConfig,
    *,
    arg_name: str,
    verbose: bool,
) -> None:
    """
    Merge a list-like option, preferring the CLI value when present.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed command-line arguments to update in place.
    config : LintquartoConfig
        Settings loaded from `pyproject.toml`.
    arg_name : str
        Name of the attribute to merge.
    verbose : bool
        If `True`, print the source of the final value.
    """
    cli_val = getattr(args, arg_name)
    config_val = getattr(config, arg_name)

    if cli_val:
        if verbose:
            print(
                f"  - {arg_name}: from CLI "
                f"(ignoring [tool.lintquarto]): {cli_val}"
            )
        return

    if config_val:
        setattr(args, arg_name, config_val)
        if verbose:
            print(f"  - {arg_name}: from [tool.lintquarto]: {config_val}")


def _merge_additive(
    args: argparse.Namespace,
    config: LintquartoConfig,
    *,
    arg_name: str,
    verbose: bool,
) -> None:
    """
    Merge an additive list-like option from config and CLI.

    Config values are prepended and CLI values are appended. Items already
    present in the CLI value are not duplicated.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed command-line arguments to update in place.
    config : LintquartoConfig
        Settings loaded from `pyproject.toml`.
    arg_name : str
        Name of the attribute to merge.
    verbose : bool
        If `True`, print the merged value.
    """
    cli_vals = list(getattr(args, arg_name) or [])
    config_vals = getattr(config, arg_name)
    merged = [v for v in config_vals if v not in cli_vals] + cli_vals
    setattr(args, arg_name, merged)

    if verbose and merged:
        print(f"  - {arg_name}: merged from [tool.lintquarto] + CLI: {merged}")


def _merge_bool_or(
    args: argparse.Namespace,
    config: LintquartoConfig,
    *,
    flag: str,
    verbose: bool,
) -> None:
    """
    Merge a boolean option using OR semantics.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed command-line arguments to update in place.
    config : LintquartoConfig
        Settings loaded from `pyproject.toml`.
    flag : str
        Name of the boolean attribute to merge.
    verbose : bool
        If `True`, print when the config enables a flag that was not set on
        the CLI.
    """
    cli_val = getattr(args, flag)
    config_val = getattr(config, flag)
    merged = cli_val or config_val
    setattr(args, flag, merged)

    if verbose and config_val and not cli_val:
        print(f"  - {flag}: from [tool.lintquarto]: {config_val}")
