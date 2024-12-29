from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Définissez le module des paramètres Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

app = Celery('myproject')

# Lisez la configuration de Celery depuis settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Recherchez automatiquement les tâches dans vos applications Django
app.autodiscover_tasks()
