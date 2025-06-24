# streamlit_app.py
"""Universal Streamlit dashboard to orchestrate **any** review‑handling scripts.

🔹 **Zero subprocess calls** – scripts are imported and executed in‑process.
🔹 **Pluggable** – drop any `*.py` tool in the `scripts/` folder and it will appear as a tab.
🔹 **Generic** – no hard‑coded host, site name, or replacement word; the UI lets you set them.

---
Running the app:
```bash
pip install streamlit pandas importlib_metadata
streamlit run streamlit_app.py
```

Folder layout expected:
```
project/
├── streamlit_app.py   # ⇐ this file
└── scripts/           # your tools live here
    ├── Extract.py
    ├── Insert_rates.py
    └── ...
```
Each script **must** expose a `cli(parser)` function that receives an `argparse.ArgumentParser` and registers its options,
**or** a traditional `main()` accepting `sys.argv` – both patterns are auto‑detected.
"""

from __future__ import annotations
import contextlib, importlib.util, io, runpy, sys, types, pathlib, inspect
import streamlit as st
import pandas as pd
from datetime import datetime as dt
from collections.abc import Generator



ROOT = pathlib.Path(__file__).parent
SCRIPTS_DIR = ROOT / "scripts"

# --------------------------------------------------------------------------------------
# Dynamic discovery helpers
# --------------------------------------------------------------------------------------

def discover_scripts() -> dict[str, pathlib.Path]:
    """Return {name: path} for every *.py in /scripts"""
    return {
        p.stem: p for p in sorted(SCRIPTS_DIR.glob("*.py"), key=lambda p: p.name.lower())
    }


def import_module_from_path(path: pathlib.Path) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise ImportError(f"Cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = mod
    spec.loader.exec_module(mod)  # type: ignore[arg-type]
    return mod


@contextlib.contextmanager
def capture_stdout() -> Generator[tuple[io.StringIO, io.StringIO], None, None]:
    buf_out, buf_err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
        yield buf_out, buf_err


# --------------------------------------------------------------------------------------
# UI helpers
# --------------------------------------------------------------------------------------

def show_csv(path: pathlib.Path, n: int = 20):
    try:
        df = pd.read_csv(path)
        st.dataframe(df.head(n))
    except Exception as exc:
        st.warning(f"Could not load CSV: {exc}")


def execute_script(mod: types.ModuleType, argv: list[str]):
    """Executes a tool module with given argv; returns (stdout, stderr, rc)."""
    rc = 0
    with capture_stdout() as (out, err):
        old_argv = sys.argv.copy()
        try:
            sys.argv = [mod.__name__] + argv
            if hasattr(mod, "cli"):
                # Advanced style: cli(argparse_parser) → Namespace
                import argparse

                parser = argparse.ArgumentParser()
                ns = mod.cli(parser)  # type: ignore[arg-type]
                args = parser.parse_args(argv)
                if hasattr(mod, "main"):
                    rc = mod.main(args) or 0  # type: ignore[arg-type]
            elif hasattr(mod, "main"):
                rc = mod.main() or 0  # type: ignore[func-returns-value]
            else:
                runpy.run_path(mod.__file__, run_name="__main__")  # type: ignore[arg-type]
        except SystemExit as e:
            rc = e.code or 0
        finally:
            sys.argv = old_argv
    return out.getvalue(), err.getvalue(), rc


# --------------------------------------------------------------------------------------
# Streamlit UI
# --------------------------------------------------------------------------------------

st.set_page_config(page_title="Universal Review Toolkit", layout="wide")

st.sidebar.header("Global settings")

def text_setting(key: str, default: str = "") -> str:
    return st.sidebar.text_input(key, value=default, key=f"sidebar_{key}")

mysql_host = text_setting("MySQL host")
mysql_user = text_setting("MySQL user")
mysql_pwd = text_setting("MySQL password")
mysql_db = text_setting("MySQL database")

dry_run = st.sidebar.checkbox("Dry‑run (simulate)")

st.sidebar.markdown("---")

scripts = discover_scripts()
if not scripts:
    st.warning("Drop your tool scripts into the /scripts folder and refresh.")
    st.stop()

# Create one tab per script dynamically
script_tabs = st.tabs([f"🛠️ {label}" for label in scripts])

for (name, path), tab in zip(scripts.items(), script_tabs):
    with tab:
        st.subheader(f"Tool: `{name}`")
        code_expander = st.expander("Show code", False)
        with code_expander:
            code = path.read_text(encoding="utf-8")
            st.code(code, language="python")

        # Generic arg input
        args_str = st.text_input("Arguments (as you would on CLI)", key=f"args_{name}")
        argv = [arg for arg in args_str.split() if arg]

        if st.button("Run", key=f"run_{name}"):
            mod = import_module_from_path(path)
            st.code(f"python {path.name} {' '.join(argv)}")
            with st.spinner("Running…"):
                out, err, rc = execute_script(mod, argv)
            st.text(out or "(no stdout)")
            if err:
                st.error(err)
            st.success(f"Exit code: {rc}")
            # Auto‑preview CSV outputs written to cwd in this session
            csv_files = list(ROOT.glob("*.csv"))
            if csv_files:
                st.write("Detected CSV file(s):")
                for csv_path in csv_files:
                    show_csv(csv_path)

st.sidebar.success("Ready – plug any script, run anywhere ✨")
