from django.apps import AppConfig


class BackendConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "backend"

    def ready(self):
        import backend.models.signals  # noqa F401
        import backend.search.signals  # noqa F401
