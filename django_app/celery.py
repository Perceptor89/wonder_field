from celery import Celery
import os


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_app.settings')
app = Celery('django_app')
app.config_from_object('django_app.celeryconfig')
