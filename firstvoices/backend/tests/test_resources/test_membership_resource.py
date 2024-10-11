import uuid

import pytest
import tablib

from backend.models.constants import AppRole, Role
from backend.resources.app import AppMembership, AppMembershipResource
from backend.resources.sites import Membership, MembershipResource
from backend.tests.factories import (
    AppMembershipFactory,
    MembershipFactory,
    SiteFactory,
    UserFactory,
)


@pytest.mark.skip("Tests are for initial migration only")
class TestAppMembershipImport:
    @staticmethod
    def build_table(data: list[str]):
        headers = [
            # these headers should match what is produced by fv-nuxeo-export tool
            "user,created,created_by,last_modified,last_modified_by,id,role",
        ]
        table = tablib.import_set("\n".join(headers + data), format="csv")
        return table

    @pytest.mark.django_db
    def test_import_base_data(self):
        """Import AppMembership object with basic fields"""
        id_one = uuid.uuid4()
        user = UserFactory.create()
        data = [
            f"{user.email},,,,,{id_one},Staff",
        ]
        table = self.build_table(data)
        result = AppMembershipResource().import_data(dataset=table)

        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["new"] == len(data)
        new_membership = AppMembership.objects.filter(id=table["id"][0])
        assert new_membership.exists()
        assert new_membership.first().user == user
        assert new_membership.first().role == AppRole.STAFF
        assert new_membership.first().created_by.email == "support@fpcc.ca"

    @pytest.mark.django_db
    def test_no_overwrite(self):
        """Only new roles should be added, existing should not be overwritten"""
        user = UserFactory.create()
        AppMembershipFactory.create(user=user, role=AppRole.SUPERADMIN)

        id_one = uuid.uuid4()
        data = [
            f"{user.email},,,,,{id_one},Staff",
        ]
        table = self.build_table(data)
        result = AppMembershipResource().import_data(dataset=table)

        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["new"] == 0
        assert result.totals["skip"] == 1
        old_membership = AppMembership.objects.get(user=user)
        assert old_membership.role == AppRole.SUPERADMIN


@pytest.mark.skip("Tests are for initial migration only")
class TestSiteMembershipImport:
    @staticmethod
    def build_table(data: list[str]):
        headers = [
            # these headers should match what is produced by fv-nuxeo-export tool
            "user,role,order,id,created,created_by,last_modified,last_modified_by,site",
        ]
        table = tablib.import_set("\n".join(headers + data), format="csv")
        return table

    @pytest.mark.django_db
    def test_import_base_data(self):
        """Import site-level Membership object with basic fields"""
        site = SiteFactory.create()
        user = UserFactory.create()
        id_one = uuid.uuid4()
        data = [
            f"{user.email},Language Admin,0,{id_one},,,,,{site.id}",
        ]
        table = self.build_table(data)
        result = MembershipResource().import_data(dataset=table)

        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["new"] == len(data)
        assert Membership.objects.filter(site=site.id).count() == len(data)

        new_membership = Membership.objects.filter(id=table["id"][0])
        assert new_membership.exists()
        assert new_membership.first().user == user
        assert new_membership.first().role == Role.LANGUAGE_ADMIN
        assert new_membership.first().created_by.email == "support@fpcc.ca"

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "exporter_label,django_choice",
        [
            ("Language Admin", Role.LANGUAGE_ADMIN),
            ("Editor", Role.EDITOR),
            ("Assistant", Role.ASSISTANT),
            ("Member", Role.MEMBER),
        ],
    )
    def test_import_all_roles(self, exporter_label, django_choice):
        """Ensure that import works for all site membership roles"""
        site = SiteFactory.create()
        user = UserFactory.create()
        id_one = uuid.uuid4()
        data = [
            f"{user.email},{exporter_label},0,{id_one},,,,,{site.id}",
        ]
        table = self.build_table(data)
        result = MembershipResource().import_data(dataset=table)

        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["new"] == len(data)
        new_membership = Membership.objects.filter(id=table["id"][0])
        assert new_membership.exists()
        assert new_membership.first().role == django_choice

    @pytest.mark.django_db
    def test_skip_existing(self):
        """Import skips memberships that already exist in the database"""
        site = SiteFactory.create()
        user = UserFactory.create()
        MembershipFactory.create(user=user, site=site, role=Role.LANGUAGE_ADMIN)

        id_one = uuid.uuid4()
        data = [
            f"{user.email},Language Admin,0,{id_one},,,,,{site.id}",
        ]
        table = self.build_table(data)
        result = MembershipResource().import_data(dataset=table)

        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["skip"] == len(data)
        assert Membership.objects.filter(user=user, site=site).count() == 1
