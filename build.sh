#!/usr/bin/env bash
# Ensures the build script exits immediately if any command fails.
set -o errexit

# Installs required Python dependencies specified in requirements.txt.
pip install -r requirements.txt

# Collects static files (CSS, JS) from all apps into the STATIC_ROOT directory.
python manage.py collectstatic --no-input

# Applies database schema migrations to the remote database (e.g., Neon PostgreSQL).
python manage.py migrate