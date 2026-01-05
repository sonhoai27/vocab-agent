uv venv --python 3.12
source .venv/bin/activate
uv pip freeze > requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1
