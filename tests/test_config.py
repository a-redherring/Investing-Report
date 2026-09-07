import pytest

from investment_system.config import (
    CONFIG_DIR_ENV_VAR,
    load_model_config,
    load_universe,
    resolve_config_dir,
    resolve_repo_root,
)


def test_load_model_config_reads_committed_yaml():
    config = load_model_config()
    assert config.model_version == "1.0"
    assert config.cash_yield_pct == 5.0
    assert config.brokerage.minimum_aud == 11.0
    assert config.brokerage.rate_pct == 0.10
    assert config.brokerage.qualifying_buy_limit_aud == 999.0


def test_load_universe_reads_committed_yaml():
    universe = load_universe()
    symbols = {asset["symbol"] for asset in universe}
    assert symbols == {"IVV", "NDQ", "VAS", "VGS", "IZZ", "VAE", "GOLD", "BTC", "CASH"}
    core_symbols = {asset["symbol"] for asset in universe if asset["core"]}
    assert core_symbols == {"IVV", "VAS", "VGS", "VAE"}


def _write_minimal_config(config_dir):
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "model-v1.0.yaml").write_text(
        "model_version: \"9.9\"\ncash_yield_pct: 1.0\nbrokerage:\n  minimum_aud: 1.0\n  rate_pct: 1.0\n  qualifying_buy_limit_aud: 1.0\n"
    )
    (config_dir / "universe.yaml").write_text("assets:\n  - {symbol: X, currency: AUD, core: false}\n")


def test_env_var_override_takes_priority(tmp_path, monkeypatch):
    _write_minimal_config(tmp_path / "myconfig")
    monkeypatch.setenv(CONFIG_DIR_ENV_VAR, str(tmp_path / "myconfig"))
    assert resolve_config_dir() == tmp_path / "myconfig"
    assert load_model_config().model_version == "9.9"
    assert load_universe() == [{"symbol": "X", "currency": "AUD", "core": False}]


def test_env_var_pointing_at_a_directory_without_the_file_fails_closed(tmp_path, monkeypatch):
    monkeypatch.setenv(CONFIG_DIR_ENV_VAR, str(tmp_path))  # empty directory, no model-v1.0.yaml
    with pytest.raises(FileNotFoundError, match=CONFIG_DIR_ENV_VAR):
        resolve_config_dir()


def test_falls_back_to_a_config_directory_under_the_current_working_directory(tmp_path, monkeypatch):
    monkeypatch.delenv(CONFIG_DIR_ENV_VAR, raising=False)
    _write_minimal_config(tmp_path / "config")
    monkeypatch.chdir(tmp_path)
    assert resolve_config_dir() == tmp_path / "config"


def test_walks_up_parent_directories_to_find_config(tmp_path, monkeypatch):
    monkeypatch.delenv(CONFIG_DIR_ENV_VAR, raising=False)
    _write_minimal_config(tmp_path / "config")
    nested = tmp_path / "a" / "b" / "c"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)
    assert resolve_config_dir() == tmp_path / "config"


def test_resolve_repo_root_fails_closed_with_an_actionable_message(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(FileNotFoundError, match="checkout of this repository"):
        resolve_repo_root("definitely-not-a-real-marker-file.xyz")
