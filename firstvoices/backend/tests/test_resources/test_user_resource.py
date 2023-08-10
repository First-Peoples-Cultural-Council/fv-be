import pytest
import tablib
from jwt_auth.models import User

from backend.resources.users import UserResource


def build_table(data: list[str]):
    headers = [
        # these headers should match what is produced by fv-nuxeo-export tool
        "username,first_name,last_name,email",
    ]
    table = tablib.import_set("\n".join(headers + data), format="csv")
    return table


class TestUserImport:
    @pytest.mark.django_db
    def test_import_base_data(self):
        """Import User object with basic fields"""
        data = [
            "my_email@example.com,Sample,Smith,my_email@example.com",  # noqa E501
            "your_email@example.com,Testy,Tot,your_email@example.com",  # noqa E501
        ]
        table = build_table(data)

        result = UserResource().import_data(dataset=table)

        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["new"] == len(data)
        assert User.objects.count() == len(data)

        assert User.objects.filter(email=table["email"][0]).exists()
        assert User.objects.filter(email=table["email"][1]).exists()
