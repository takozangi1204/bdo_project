#!/usr/bin/env bash
# Ensures the build script exits immediately if any command fails.
set -o errexit

# Installs required Python dependencies specified in requirements.txt.
pip install -r requirements.txt

# Collects static files (CSS, JS) from all apps into the STATIC_ROOT directory.
python manage.py collectstatic --no-input

# Applies database schema migrations to the remote database (e.g., Neon PostgreSQL).
python manage.py migrate

# Auto-creates superuser ONLY if DJANGO_SUPERUSER_USERNAME and DJANGO_SUPERUSER_PASSWORD are set in secure environment variables
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "Creating superuser '${DJANGO_SUPERUSER_USERNAME}' from environment variables..."
    python manage.py createsuperuser --no-input || true
else
    echo "Notice: DJANGO_SUPERUSER_PASSWORD is not set. Skipping automated superuser creation for security."
fi