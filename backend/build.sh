#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "==> Upgrading pip..."
pip install --upgrade pip

echo "==> Installing Python dependencies with --no-cache-dir..."
pip install --no-cache-dir -r requirements.txt

echo "==> Collecting static files..."
python manage.py collectstatic --no-input

echo "==> Applying database migrations..."
python manage.py migrate

echo "==> Ensuring initial superuser (if credentials provided in env)..."
python manage.py create_initial_admin

echo "==> Build completed successfully!"
