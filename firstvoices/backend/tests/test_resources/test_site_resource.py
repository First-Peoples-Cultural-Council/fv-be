import uuid
from datetime import datetime

import pytest
import tablib
from django.utils import timezone

from backend.models.constants import Visibility
from backend.models.sites import Site
from backend.resources.sites import SiteMigrationResource, SiteResource
from backend.tests.factories import LanguageFactory, SiteFactory, UserFactory


def build_table(data: list[str]):
    headers = [
        # these headers should match what is produced by fv-nuxeo-export tool
        "id,created,created_by,last_modified,last_modified_by,title,slug,visibility,language,contact_email",
    ]
    table = tablib.import_set("\n".join(headers + data), format="csv")
    return table


class TestSiteImport:
    @pytest.mark.django_db
    def test_import_base_data(self):
        """Import Site object with basic fields"""
        user1 = UserFactory.create()
        user2 = UserFactory.create()
        test_language = LanguageFactory.create(title="Testese")
        data = [
            f"{uuid.uuid4()},2023-02-02 21:21:10.713,{user1.email},2023-02-02 21:21:39.864,{user2.email},AckAck Site,ackack,Public,Testese,test@email.com",  # noqa E501
            f"{uuid.uuid4()},2023-02-16 21:03:16.196,{user2.email},2023-02-27 22:58:33.739,{user2.email},Mudpuddle,mudpuddle,Team,,",  # noqa E501
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
        assert new_site.language == test_language
        assert new_site.contact_email == table["contact_email"][0]

        new_site = Site.objects.get(id=table["id"][1])
        assert new_site.visibility == Visibility.TEAM

    @pytest.mark.django_db
    def test_import_metadata_custom_timestamps(self):
        """
        Allow manual created/modified dates when creating object from import,
        but update last_modified if changed later.
        """
        site_id = uuid.uuid4()
        data = [
            f"{site_id},2023-02-02 21:21:10.713,test@example.com,2023-02-02 21:21:39.864,test@example.com,Updated,updated,Members,,",  # noqa E501
        ]
        table = build_table(data)

        result = SiteResource().import_data(dataset=table)
        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["new"] == 1

        new_site = Site.objects.get(id=table["id"][0])
        assert new_site.created == datetime.fromisoformat(
            table["created"][0]
        ).astimezone(timezone.get_default_timezone())
        assert new_site.last_modified == datetime.fromisoformat(
            table["last_modified"][0]
        ).astimezone(timezone.get_default_timezone())

        # update last_modified on update
        old_created = new_site.created
        old_last_modified = new_site.last_modified
        new_site.title = "My Updated Site Title 12364"
        new_site.save()
        assert new_site.created == old_created
        assert new_site.last_modified != old_last_modified

    @pytest.mark.django_db
    def test_import_metadata_missing_user(self):
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
        # for now: use dummy user details on migrated site - fix later to match actual data
        assert new_site.created_by.email == "support@fpcc.ca"


class TestSiteMigration:
    @pytest.mark.django_db
    def test_delete_site_before_import(self):
        """Import a Site object when a site with that UID already exists."""
        orig_site = SiteFactory.create(title="Original")
        data = [
            f"{orig_site.id},2023-02-02 21:21:10.713,test@example.com,2023-02-02 21:21:39.864,test@example.com,Updated,updated,Members",  # noqa E501
        ]
        table = build_table(data)

        result = SiteMigrationResource().import_data(dataset=table)

        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["new"] == 1
        site_at_id = Site.objects.get(id=orig_site.id)
        assert site_at_id.title == table["title"][0]
