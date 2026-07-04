from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_model_name_matches_existing_project_convention() -> None:
    env_example = (ROOT / ".env.example").read_text()
    hermes_config = (ROOT / "config" / "hermes-config.yaml").read_text()

    assert "MODEL_NAME=" in env_example
    assert "OPENAI_MODEL=" not in env_example
    assert "__MODEL_NAME__" in hermes_config
    assert "__OPENAI_MODEL__" not in hermes_config
    assert "__OPENAI_BASE_URL__" in hermes_config


def test_local_hermes_auth_is_optional_and_blank_by_default() -> None:
    env_example = (ROOT / ".env.example").read_text()

    assert "HERMES_API_KEY=\n" in env_example


def test_relay_key_is_explicitly_bound_to_named_custom_provider() -> None:
    hermes_config = (ROOT / "config" / "hermes-config.yaml").read_text()

    assert "provider: custom:zc-relay" in hermes_config
    assert "name: zc-relay" in hermes_config
    assert "key_env: OPENAI_API_KEY" in hermes_config
    assert "api_key:" not in hermes_config


def test_hermes_uses_supported_manual_approval_mode() -> None:
    hermes_config = (ROOT / "config" / "hermes-config.yaml").read_text()

    assert "mode: manual" in hermes_config
    assert "mode: ask" not in hermes_config
