#!/usr/bin/env bash
# Ensures the build script exits immediately if any command fails.
set -o errexit

# Installs required Python dependencies specified in requirements.txt.
pip install -r requirements.txt

# Collects static files (CSS, JS) from all apps into the STATIC_ROOT directory.
python manage.py collectstatic --no-input

# Applies database schema migrations to the remote database (e.g., Neon PostgreSQL).
python manage.py migrate

# Loads initial dataset (Roadmap Phases, Tasks, Categories, Events) into remote database
echo "Loading initial data fixture..."
python manage.py loaddata initial_data.json || true

# Safe automatic superuser creation: checks if user exists before creating
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "Ensuring superuser '${DJANGO_SUPERUSER_USERNAME}' exists..."
    python manage.py shell -c "from django.contrib.auth.models import User; import os; u=os.environ.get('DJANGO_SUPERUSER_USERNAME'); p=os.environ.get('DJANGO_SUPERUSER_PASSWORD'); e=os.environ.get('DJANGO_SUPERUSER_EMAIL',''); User.objects.filter(username=u).exists() or User.objects.create_superuser(u, e, p)"
fi