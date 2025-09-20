# Gmail MCP Service

This repository contains a FastAPI based service that exposes Gmail actions (list, summarize, send) through a lightweight HTTP API designed to be consumed from Model Context Protocol (MCP) compatible clients such as ChatGPT.

## Features

- OAuth2 authentication with Gmail using the official Google API client libraries.
- Endpoints for listing messages, summarizing email content via ChatGPT, and sending emails.
- Optional sender allow list for security.
- Configuration via environment variables or a local `.env` file.

## Project layout

```
.
├── gmail_mcp_service
│   ├── __init__.py
│   ├── chatgpt_client.py
│   ├── config.py
│   ├── gmail_client.py
│   ├── main.py
│   └── service.py
├── pyproject.toml
├── README.md
└── tests
    └── test_imports.py
```

## Getting started

1. **Install dependencies**

   ```bash
   pip install -e .[development]
   ```

2. **Create Google OAuth credentials**

   - Visit the [Google Cloud Console](https://console.cloud.google.com/) and create an OAuth client (Desktop application).
   - Download the `client_secret.json` file and store it locally.

3. **Prepare environment variables**

   Create a `.env` file in the project root containing:

   ```env
   GOOGLE_CLIENT_SECRET_FILE=/absolute/path/to/client_secret.json
   GMAIL_TOKEN_FILE=/absolute/path/to/token.json
   OPENAI_API_KEY=sk-your-openai-key
   OPENAI_MODEL=gpt-4o-mini
   ALLOWED_SENDERS=trusted@example.com,another@example.com
   ```

   The `GMAIL_TOKEN_FILE` will be generated automatically after the first successful OAuth flow.

4. **Run the development server**

   ```bash
   uvicorn gmail_mcp_service.main:app --reload
   ```

   The service listens on `http://localhost:8000`. Swagger docs are available at `/docs`.

5. **Configure ChatGPT MCP client**

   In a ChatGPT MCP compatible client, add a tool configuration similar to:

   ```json
   {
     "schema_version": "v1",
     "name": "gmail",
     "url": "http://localhost:8000",
     "capabilities": {
       "listMessages": {
         "method": "GET",
         "path": "/messages"
       },
       "summarizeMessage": {
         "method": "POST",
         "path": "/summaries"
       },
       "sendEmail": {
         "method": "POST",
         "path": "/send"
       }
     }
   }
   ```

   Refer to your MCP client documentation for the exact configuration syntax.

## Security considerations

- Restrict which senders can be processed via the `ALLOWED_SENDERS` environment variable.
- Use per-user OAuth credentials and avoid sharing tokens.
- Consider running the service behind HTTPS and a reverse proxy in production.

## Testing

Run the test suite with:

```bash
pytest
```
