from django.apps import AppConfig


class VmsAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'vms_app'

    def ready(self):
        import vms_app.signals
