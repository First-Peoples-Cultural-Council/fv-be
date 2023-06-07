import uuid

import pytest
import tablib

from backend.models.constants import Visibility
from backend.models.sites import Site
from backend.models.user import User
from backend.resources.sites import SiteResource
from backend.tests.factories import UserFactory


def build_table(data: list[str]):
    headers = [
        # these headers should match what is produced by fv-nuxeo-export tool
        "id,created,created_by,last_modified,last_modified_by,title,slug,visibility",
    ]
    table = tablib.import_set("\n".join(headers + data), format="csv")
    return table


class TestSiteImport:
    # Import errors can be debugged with param raise_errors=True in import_data
    @pytest.mark.django_db
    def test_import_basic(self):
        """Import Site object with basic fields"""
        user1 = UserFactory.create()
        user2 = UserFactory.create()
        data = [
            f"{uuid.uuid4()},2023-02-02 21:21:10.713,{user1.email},2023-02-02 21:21:39.864,{user2.email},AckAck Site,ackack,Public",  # noqa E501
            f"{uuid.uuid4()},2023-02-16 21:03:16.196,{user2.email},2023-02-27 22:58:33.739,{user2.email},Mudpuddle,mudpuddle,Team",  # noqa E501
        ]
        table = build_table(data)

        result = SiteResource().import_data(dataset=table)

        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["new"] == 2
        new_site = Site.objects.get(id=table["id"][0])
        assert new_site.title == table["title"][0]
        assert new_site.slug == table["slug"][0]
        assert new_site.created_by.email == table["created_by"][0]
        assert new_site.last_modified_by.email == table["last_modified_by"][0]
        assert new_site.visibility == Visibility.PUBLIC
        new_site = Site.objects.get(id=table["id"][1])
        assert new_site.visibility == Visibility.TEAM

    @pytest.mark.django_db
    def test_import_with_missing_user(self):
        """Import a Site object with an unrecognized user in metadata"""
        email = "u2@example.com"
        data = [
            f"{uuid.uuid4()},2023-02-02 21:21:10.713,{email},2023-02-02 21:21:39.864,{email},Samply,samply,Team",  # noqa E501
        ]
        table = build_table(data)

        result = SiteResource().import_data(dataset=table)

        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["new"] == 1
        new_site = Site.objects.get(id=table["id"][0])
        assert new_site.created_by.email == table["created_by"][0]
        matching_users = User.objects.filter(email=email)
        assert matching_users.count() == 1
        assert matching_users[0].id == email
