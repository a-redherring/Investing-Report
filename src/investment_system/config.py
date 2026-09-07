from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml

CONFIG_DIR_ENV_VAR = "INVESTMENT_SYSTEM_CONFIG_DIR"

# Fallback for an editable/source-tree install: src/investment_system/config.py
# -> parents[2] is the repository root, regardless of the current working
# directory. This is only reached if neither the env var nor cwd resolution
# below finds anything, so it's harmless for a non-editable wheel install
# (there's simply no sibling config/ to find there either).
_PACKAGE_SRC_ROOT = Path(__file__).resolve().parents[2]


def resolve_repo_root(marker_relative_path: str) -> Path:
    """Locate the checked-out repository root containing `marker_relative_path`.

    Tried in order: the current working directory and its parents (the
    documented workflow — run commands from within a clone of this repo, or a
    subdirectory of one; this is also what lets an MCP server pointed at an
    operator's own clone work regardless of install mode), then the path
    relative to this installed package (works for an editable/source install
    even if invoked from an unrelated cwd). Resolved fresh on every call, not
    cached at import time.
    """
    candidates = [Path.cwd(), *Path.cwd().parents, _PACKAGE_SRC_ROOT]
    seen: set[Path] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if (candidate / marker_relative_path).is_file():
            return candidate
    searched = ", ".join(str(candidate) for candidate in seen)
    raise FileNotFoundError(f"could not find {marker_relative_path} under any of: {searched}. Run from within a checkout of this repository, or set {CONFIG_DIR_ENV_VAR}.")


def resolve_config_dir() -> Path:
    """Locate the directory holding model-v1.0.yaml / universe.yaml.

    Honours the INVESTMENT_SYSTEM_CONFIG_DIR environment variable first (an
    explicit override, e.g. for an MCP server or a non-editable install
    pointed at an operator's own clone); otherwise falls back to
    resolve_repo_root()'s cwd/package search for a `config/` directory.
    """
    override = os.environ.get(CONFIG_DIR_ENV_VAR)
    if override:
        override_dir = Path(override)
        if not (override_dir / "model-v1.0.yaml").is_file():
            raise FileNotFoundError(f"{CONFIG_DIR_ENV_VAR}={override!r} does not contain model-v1.0.yaml")
        return override_dir
    return resolve_repo_root("config/model-v1.0.yaml") / "config"


@dataclass(frozen=True)
class BrokerageConfig:
    minimum_aud: float
    rate_pct: float
    qualifying_buy_limit_aud: float


@dataclass(frozen=True)
class ModelConfig:
    model_version: str
    cash_yield_pct: float
    brokerage: BrokerageConfig


def load_model_config(path: str | Path | None = None) -> ModelConfig:
    config_path = Path(path) if path is not None else resolve_config_dir() / "model-v1.0.yaml"
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    brokerage = data["brokerage"]
    return ModelConfig(
        model_version=str(data["model_version"]),
        cash_yield_pct=float(data["cash_yield_pct"]),
        brokerage=BrokerageConfig(
            minimum_aud=float(brokerage["minimum_aud"]),
            rate_pct=float(brokerage["rate_pct"]),
            qualifying_buy_limit_aud=float(brokerage["qualifying_buy_limit_aud"]),
        ),
    )


def load_universe(path: str | Path | None = None) -> list[dict[str, object]]:
    config_path = Path(path) if path is not None else resolve_config_dir() / "universe.yaml"
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    return list(data["assets"])
