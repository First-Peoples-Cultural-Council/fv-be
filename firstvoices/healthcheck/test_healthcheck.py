import pytest
from rest_framework.test import APIClient

from backend.tests import factories


class TestHealthcheck:
    def setup_method(self):
        self.client = APIClient()
        self.user = factories.UserFactory.create()

    @pytest.mark.django_db
    def test_healthcheck(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/health")
        assert response.status_code == 200
        assert response.json() == {
            "status": "server is ok",
            "build": "local",
            "environment": "local",
        }
