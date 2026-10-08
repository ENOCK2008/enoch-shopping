#!/usr/bin/env bash
set -o errexit
pip install -r requirements.txt
python manage.py makemigrations users sellers catalog cart orders reviews messaging localization payments shipping notifications
python manage.py migrate
python manage.py collectstatic --no-input
