#!/usr/bin/env bash
set -e

# On a fresh volume MySQL reports "healthy" while still finishing first-run init
# and may briefly refuse connections. Wait until it truly accepts our connection.
echo "Waiting for MySQL to accept connections..."
tries=0
until python -c "import os,sqlalchemy; sqlalchemy.create_engine(os.environ['DATABASE_URL']).connect().close()" 2>/dev/null; do
  tries=$((tries + 1))
  if [ "$tries" -ge 40 ]; then
    echo "MySQL not reachable after 80s, giving up." >&2
    exit 1
  fi
  sleep 2
done
echo "MySQL ready."

alembic upgrade head
python scripts/seed_products.py   # idempotent: populates the catalog on first run
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
