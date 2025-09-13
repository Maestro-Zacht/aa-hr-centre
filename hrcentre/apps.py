from django.apps import AppConfig

from hrcentre import __version__ as version


class HRCentreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hrcentre'
    verbose_name = f'HR Centre v{version}'
