import uuid

import pytest
import tablib

from backend.models import JoinRequest
from backend.resources.join_requests import JoinRequestResource
from backend.tests import factories


@pytest.mark.skip("Tests are for initial migration only")
class TestJoinRequestImport:
    @staticmethod
    def build_table(data: list[str]):
        headers = [
            # these headers should match what is produced by fv-nuxeo-export tool
            "id,created,created_by,last_modified,last_modified_by,site,"
            "user,reason_note,status,reasons",
        ]
        table = tablib.import_set("\n".join(headers + data), format="csv")
        return table

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "reasons,expected_reason_count",
        [
            ('"LANGUAGE_LEARNER"', 1),
            ('"LANGUAGE_LEARNER,COMMUNITY_MEMBER,HERITAGE"', 3),
        ],
    )
    def test_import_base_data(self, reasons, expected_reason_count):
        """Import JoinRequest object with basic fields and single/multiple reasons"""
        site = factories.SiteFactory.create()
        user = factories.UserFactory.create()
        data = [
            f"{uuid.uuid4()},2021-04-09 22:52:17.460,{user.email},2021-04-09 22:52:17.460,{user.email},{site.id},"
            f"{user.email},reason note,PENDING,{reasons}",
        ]
        table = self.build_table(data)

        result = JoinRequestResource().import_data(dataset=table)

        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["new"] == len(data)
        assert JoinRequest.objects.count() == len(data)

        assert JoinRequest.objects.filter(id=table["id"][0]).exists()
        join_request = JoinRequest.objects.get(id=table["id"][0])
        assert join_request.user == user
        assert join_request.site == site
        assert join_request.reasons_set.count() == expected_reason_count
        assert join_request.get_status_display().lower() == "pending"
        assert join_request.reason_note == "reason note"

    @pytest.mark.django_db
    def test_import_skip_unknown_user(self):
        """Import JoinRequest object with unknown user, should skip row"""
        site = factories.SiteFactory.create()
        data = [
            f"{uuid.uuid4()},2021-04-09 22:52:17.460,user_one@test.com,2021-04-09 22:52:17.460,user_one@test.com,"
            f'{site.id},user_one@test.com,reason note,PENDING,"LANGUAGE_LEARNER"',
        ]
        table = self.build_table(data)

        result = JoinRequestResource().import_data(dataset=table)

        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["skip"] == len(data)
        assert JoinRequest.objects.count() == 0

    @pytest.mark.django_db
    def test_import_skip_unknown_site(self):
        """Import JoinRequest object with unknown site, should skip row"""
        unknown_site_id = uuid.uuid4()
        user = factories.UserFactory.create()
        data = [
            f"{unknown_site_id},2021-04-09 22:52:17.460,{user.email},2021-04-09 22:52:17.460,{user.email},"
            f"{unknown_site_id},"
            f'{user.email},reason note,PENDING,"LANGUAGE_LEARNER"',
        ]
        table = self.build_table(data)

        result = JoinRequestResource().import_data(dataset=table)

        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["skip"] == len(data)
        assert JoinRequest.objects.count() == 0

    @pytest.mark.django_db
    def test_skip_existing_join_requests(self):
        """Import JoinRequest object with existing join request, should skip row"""
        site = factories.SiteFactory.create()
        user = factories.UserFactory.create()
        factories.JoinRequestFactory.create(site=site, user=user)
        data = [
            f"{site.id},2021-04-09 22:52:17.460,{user.email},2021-04-09 22:52:17.460,{user.email},"
            f"{site.id},"
            f'{user.email},reason note,PENDING,"LANGUAGE_LEARNER"',
        ]
        table = self.build_table(data)

        result = JoinRequestResource().import_data(dataset=table)

        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["skip"] == len(data)
        assert JoinRequest.objects.count() == 1
