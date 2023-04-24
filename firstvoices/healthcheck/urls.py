from django.urls import path

from .views import HealthCheckView

urlpatterns = [
    path(r"health", HealthCheckView.as_view()),
]
