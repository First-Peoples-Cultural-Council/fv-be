import pytest

from backend.tests import factories


class TestOrganizationModel:
    @pytest.mark.django_db
    def test_representation(self):
        site = factories.SiteFactory(visibility=factories.Visibility.PUBLIC)
        organization = factories.OrganizationFactory(site=site)

        expected_str = organization.name
        assert str(organization) == expected_str
