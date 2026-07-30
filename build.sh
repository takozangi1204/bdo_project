#!/usr/bin/env bash
# Ensures the build script exits immediately if any command fails.
set -o errexit

# Installs required Python dependencies specified in requirements.txt.
pip install -r requirements.txt

# Collects static files (CSS, JS) from all apps into the STATIC_ROOT directory.
python manage.py collectstatic --no-input

# Applies database schema migrations to the remote database (e.g., Neon PostgreSQL).
python manage.py migrate

# Auto-creates superuser with default fallback credentials (admin / 112233zZ!!) if not explicitly set
export DJANGO_SUPERUSER_USERNAME="${DJANGO_SUPERUSER_USERNAME:-admin}"
export DJANGO_SUPERUSER_PASSWORD="${DJANGO_SUPERUSER_PASSWORD:-112233zZ!!}"
export DJANGO_SUPERUSER_EMAIL="${DJANGO_SUPERUSER_EMAIL:-admin@example.com}"

echo "Ensuring superuser '${DJANGO_SUPERUSER_USERNAME}' exists..."
python manage.py createsuperuser --no-input || true