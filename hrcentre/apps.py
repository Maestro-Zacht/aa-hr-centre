from django.apps import AppConfig


class HRCentreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hrcentre'

    def ready(self):
        import hrcentre.signals
