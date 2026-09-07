from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from ..config import resolve_repo_root
from .errors import IngestionConfigError

DATA_SOURCES_RELATIVE_PATH = "config/data-sources.yaml"


def load_data_sources_config(path: str | Path | None = None) -> dict[str, object]:
    config_path = Path(path) if path is not None else resolve_repo_root(DATA_SOURCES_RELATIVE_PATH) / DATA_SOURCES_RELATIVE_PATH
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    return dict((data or {}).get("sources", {}))


@dataclass(frozen=True)
class FinnhubConfig:
    provider: str
    base_url: str
    api_key_env_var: str
    timeout_seconds: float
    max_quote_age_seconds: float


def load_finnhub_config(path: str | Path | None = None) -> FinnhubConfig:
    sources = load_data_sources_config(path)
    data = sources.get("finnhub")
    if not data:
        raise IngestionConfigError("config/data-sources.yaml has no 'finnhub' source configured")
    return FinnhubConfig(
        provider=str(data["provider"]),
        base_url=str(data["base_url"]).rstrip("/"),
        api_key_env_var=str(data["api_key_env_var"]),
        timeout_seconds=float(data.get("timeout_seconds", 10)),
        max_quote_age_seconds=float(data.get("max_quote_age_seconds", 3600)),
    )


@dataclass(frozen=True)
class YahooConfig:
    provider: str
    base_url: str
    user_agent: str
    timeout_seconds: float


def load_yahoo_config(path: str | Path | None = None) -> YahooConfig:
    sources = load_data_sources_config(path)
    data = sources.get("yahoo")
    if not data:
        raise IngestionConfigError("config/data-sources.yaml has no 'yahoo' source configured")
    return YahooConfig(
        provider=str(data["provider"]),
        base_url=str(data["base_url"]).rstrip("/"),
        user_agent=str(data["user_agent"]),
        timeout_seconds=float(data.get("timeout_seconds", 10)),
    )
