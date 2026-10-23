# RiftDrop API

Run locally with `uvicorn app.main:app --reload` from this directory after installing `requirements.txt` into a Python 3.12+ virtual environment and copying `.env.example` to `.env`.

For local-only accounts, run `python -m app.bootstrap_demo`. It creates a super-admin and vendor without deleting data; it refuses to run in production.

The checked-in SQLite file is prototype data only. Do not use it for production. Production requires PostgreSQL migrations, M-Pesa callback network allowlisting, and a shared WebSocket/event broker before multi-worker launch.

