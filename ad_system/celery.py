# ad_system/celery.py
import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ad_system.settings')

# Create a Celery application instance.
app = Celery('ad_system')

# Load task modules from all registered Django app configs.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodiscover tasks in all installed Django apps.
app.autodiscover_tasks()

from celery.schedules import crontab, timedelta

# Celery Configuration
app.conf.update(
    task_acks_late=True  # Set global acks_late for all tasks
)


app.conf.beat_schedule = {
    'check_budgets': {
        'task': 'campaign.tasks.check_and_pause_overspend_campaigns',
        'schedule': crontab(minute='*/1'),
    },
    'dayparting_enforce': {
        'task': 'campaign.tasks.enforce_dayparting',
        'schedule': crontab(minute='*/15'),
    },
    'reset_daily_spend': {
        'task': 'campaign.tasks.reset_daily_spends',
        'schedule': crontab(minute=0, hour=0),
    },
    'reset_monthly_spend': {
        'task': 'campaign.tasks.reset_monthly_spends',
        'schedule': crontab(minute=0, hour=0, day_of_month=1),
    },
}
