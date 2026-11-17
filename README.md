# Przykładowy lokalny serwer MCP

## Instalacja

```
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

## Uruchomienie

```
uv run --env-file .env python server.py
```

## Dodanie do Claude Code

```
claude mcp add --transport http lot-mock-api http://127.0.0.1:9000/mcp --header "Authorization: Bearer super-secret-token-that-we-will-send-over-unecrypted-http-but-locally-so-it-is-sort-of-ok"

claude

/mcp
```

## Test: przykładowe zapytanie

```
Find me a flight from Warsaw to Lisbon on 2026-09-04, check business class availability, and hold it.
```
