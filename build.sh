#!/usr/bin/env bash
# Ensures the build script exits immediately if any command fails.
set -o errexit

# Installs required Python dependencies specified in requirements.txt.
pip install -r requirements.txt

# Collects static files (CSS, JS) from all apps into the STATIC_ROOT directory.
python manage.py collectstatic --no-input

# Applies database schema migrations to the remote database (e.g., Neon PostgreSQL).
python manage.py migrate

# Auto-creates superuser if credentials are set in environment variables
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "Creating superuser..."
    python manage.py createsuperuser --no-input || true
fi