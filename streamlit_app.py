#!/usr/bin/env python3
# streamlit_app.py
"""
Universal Review Toolkit – Streamlit dashboard (English edition)

▶️  How it works
----------------
• Every Python script placed in **/scripts** is discovered automatically.
• Parameters declared through a `cli(parser)` helper (or a global
  `argparse.ArgumentParser`) are converted to Streamlit widgets.
• Mandatory fields are marked with a *red asterisk* and execution is
  blocked until they are filled.
• The MySQL settings typed in the sidebar are injected into a script
  *only* if the script actually declares the corresponding CLI flags
  (`--host`, `--user`, `--password`, `--db`, `--dry-run`).

Usage:
    pip install streamlit pandas httpx pymysql faker
    streamlit run streamlit_app.py
"""

from __future__ import annotations

import argparse
import contextlib
import importlib.util
import inspect
import io
import pathlib
import runpy
import sys
import types
from typing import Any, Generator

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = pathlib.Path(__file__).parent
SCRIPTS_DIR = ROOT / "scripts"

# ---------------------------------------------------------------------------
# Script discovery & import helpers
# ---------------------------------------------------------------------------


def discover_scripts() -> dict[str, pathlib.Path]:
    """Return a mapping {name: path} for every *.py found in /scripts."""
    return {p.stem: p for p in sorted(SCRIPTS_DIR.glob("*.py"))}


def import_module(path: pathlib.Path) -> types.ModuleType:
    """Import a Python module from its file path."""
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = mod
    spec.loader.exec_module(mod)  # type: ignore[arg-type]
    return mod


@contextlib.contextmanager
def capture() -> Generator[tuple[io.StringIO, io.StringIO], None, None]:
    """Context manager that captures stdout and stderr."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        yield out, err


# ---------------------------------------------------------------------------
# Turn argparse Actions into Streamlit widgets
# ---------------------------------------------------------------------------


def widget_for_action(action: argparse.Action, key_prefix: str) -> Any:
    """Return the appropriate Streamlit widget for an argparse Action."""
    key = f"{key_prefix}_{action.dest}"
    label = action.help or action.dest
    required = (
        (action.option_strings and getattr(action, "required", False))
        or not action.option_strings
    )
    if required:
        label = f"**:red[*]** {label}"

    # Boolean flag
    if isinstance(action, argparse._StoreTrueAction):
        return st.checkbox(label, key=key, value=False)

    # Choice list
    if action.choices:
        return st.selectbox(label, action.choices, key=key)

    # Numeric input
    typ = action.type or str
    default = action.default if action.default is not argparse.SUPPRESS else ""
    if typ in (int, float):
        step = 1 if typ is int else 0.1
        return st.number_input(
            label,
            value=default if default != "" else 0,
            step=step,
            key=key,
            format="%d" if typ is int else "%.2f",
        )

    # Fallback: plain text
    return st.text_input(label, value=default, key=key)


def build_parser(mod: types.ModuleType) -> argparse.ArgumentParser | None:
    """
    Recreate the ArgumentParser defined by the script.

    We look for a callable `cli(parser)` and invoke it to populate the parser.
    """
    if hasattr(mod, "cli") and callable(mod.cli):
        parser = argparse.ArgumentParser(add_help=False)
        mod.cli(parser)  # type: ignore[arg-type]
        return parser
    return None


def build_argv(parser: argparse.ArgumentParser, values: dict[str, Any]) -> list[str]:
    """Convert widget values into a CLI argv list suitable for the script."""
    argv: list[str] = []
    for act in parser._actions:
        if act.dest not in values:
            continue
        val = values[act.dest]

        # Boolean flag
        if isinstance(act, argparse._StoreTrueAction):
            if val:
                argv.append(act.option_strings[-1])
            continue

        # Optional argument with value
        if act.option_strings:
            if val not in ("", None):
                argv += [act.option_strings[-1], str(val)]
        else:  # Positional argument
            argv.append(str(val))
    return argv


# ---------------------------------------------------------------------------
# Execute an imported module with argv
# ---------------------------------------------------------------------------


def run_module(mod: types.ModuleType, argv: list[str]) -> tuple[str, str, int]:
    """Run a module and return (stdout, stderr, exitcode)."""
    rc = 0
    with capture() as (out, err):
        orig_argv = sys.argv.copy()
        try:
            sys.argv = [mod.__name__] + argv
            if hasattr(mod, "cli"):
                parser = argparse.ArgumentParser()
                mod.cli(parser)  # type: ignore[arg-type]
                ns = parser.parse_args(argv)
                rc = mod.main(ns) or 0  # type: ignore[arg-type]
            elif hasattr(mod, "main"):
                rc = mod.main() or 0  # type: ignore[func-returns-value]
            else:
                runpy.run_path(mod.__file__, run_name="__main__")  # type: ignore[arg-type]
        except SystemExit as e:
            rc = e.code or 0
        finally:
            sys.argv = orig_argv
    return out.getvalue(), err.getvalue(), rc


def preview_csvs():
    """Display any CSV files created in the working directory (first 15 rows)."""
    for csv_path in ROOT.glob("*.csv"):
        st.markdown(f"**Preview: `{csv_path.name}`**")
        try:
            st.dataframe(pd.read_csv(csv_path).head(15))
        except Exception as exc:
            st.error(f"Cannot open {csv_path}: {exc}")


# ---------------------------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------------------------

st.set_page_config("Universal Review Toolkit", layout="wide")

# --- Global MySQL settings (sidebar) ---------------------------------------
st.sidebar.header("MySQL – global settings")
mysql_host = st.sidebar.text_input("Host", key="mysql_host", value="")
mysql_user = st.sidebar.text_input("User", key="mysql_user", value="")
mysql_pwd = st.sidebar.text_input("Password", key="mysql_pwd", type="password")
mysql_db = st.sidebar.text_input("Database", key="mysql_db", value="")
dry_run_global = st.sidebar.checkbox("Dry-run (simulate)")
st.sidebar.markdown("---")

# --- Discover available scripts -------------------------------------------
scripts = discover_scripts()
if not scripts:
    st.info("Place your *.py tools inside the /scripts folder and refresh.")
    st.stop()

tabs = st.tabs([f"⚙️ {n}" for n in scripts])

for (name, path), tab in zip(scripts.items(), tabs):
    with tab:
        st.header(name)
        mod = import_module(path)
        parser = build_parser(mod)

        widget_vals: dict[str, Any] = {}
        if parser:
            st.subheader("Parameters")
            for act in parser._actions:
                if act.dest in ("help",):
                    continue  # Skip the built-in --help flag
                widget_vals[act.dest] = widget_for_action(act, f"{name}_{act.dest}")

        # --- Run button ----------------------------------------------------
        if st.button("Run", key=f"run_{name}"):
            # Check for required fields
            missing = [
                act.dest
                for act in (parser._actions if parser else [])
                if (
                    ((act.option_strings and getattr(act, "required", False))
                     or not act.option_strings)
                    and not widget_vals.get(act.dest)
                )
            ]
            if missing:
                st.error(f"Required field(s) missing: {', '.join(missing)}")
                st.stop()

            argv = build_argv(parser, widget_vals) if parser else []

            # Inject MySQL flags automatically if the script supports them
            opt_keys = set(parser._option_string_actions) if parser else set()
            for flag, val in [
                ("--host", mysql_host),
                ("--user", mysql_user),
                ("--password", mysql_pwd),
                ("--db", mysql_db),
            ]:
                if flag in opt_keys and val:
                    argv += [flag, val]
            if "--dry-run" in opt_keys and dry_run_global and "--dry-run" not in argv:
                argv.append("--dry-run")

            st.code("python " + path.name + " " + " ".join(argv))
            with st.spinner("Running…"):
                out, err, rc = run_module(mod, argv)

            st.text(out or "(no stdout)")
            if err:
                st.error(err)
            st.success(f"Exit code: {rc}")
            preview_csvs()

st.sidebar.success("Ready – plug any script & run 🚀")
