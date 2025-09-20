"""Basic smoke tests for the Gmail MCP service package."""

from gmail_mcp_service import ChatGPTClient, GmailClient, Settings, create_app


def test_create_app():
    app = create_app()
    assert app.title == "Gmail MCP Service"


def test_settings_env(tmp_path, monkeypatch):
    secret_file = tmp_path / "client_secret.json"
    secret_file.write_text("{}")
    token_file = tmp_path / "token.json"
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET_FILE", str(secret_file))
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setenv("GMAIL_TOKEN_FILE", str(token_file))
    settings = Settings()
    assert settings.google_client_secret_file == secret_file.resolve()
    assert settings.gmail_token_file == token_file.resolve()
