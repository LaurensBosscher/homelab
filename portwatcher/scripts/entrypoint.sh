#!/bin/bash
set -e

python manage.py migrate --noinput

python manage.py collectstatic --noinput

python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@localhost', 'changeme123');
    print('Created default superuser: admin/changeme123')
"

exec "$@"
