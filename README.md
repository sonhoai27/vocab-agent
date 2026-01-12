uv venv --python 3.12
source .venv/bin/activate
uv pip freeze > requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1

## History API

- `GET /history` – returns a paginated list of stored sessions. Supports filtering by `session_type`
  (`agent`, `team`, `workflow`), `user_id`, and `session_name`, and exposes metadata such as run count and
  last run timestamp.
- `GET /history/{session_id}` – returns detailed data for a session, including session state, metadata,
  and every run with its messages, metrics, and timestamps. You can also pass `session_type` and `user_id`
  to narrow the lookup.
