import pytest

from backend.models.contact_info import ContactInfo, OrganizationStatus
from backend.tests import factories


class TestContactInfoModel:
    @pytest.mark.django_db
    def test_representation(self):
        site = factories.SiteFactory(visibility=factories.Visibility.PUBLIC)
        contact_info = factories.ContactInfoFactory(site=site)

        expected_str = contact_info.organization_name
        assert str(contact_info) == expected_str

    @pytest.mark.django_db
    def test_default_values_has_no_contact_info(self):
        site = factories.SiteFactory(visibility=factories.Visibility.PUBLIC)
        contact_info = ContactInfo.objects.create(
            site=site, has_contact_information=False
        )
        contact_info.save()

        assert contact_info.emails[0] == "ltp@fpcc.ca"
        assert contact_info.url_list[0] == "https://www.firstvoices.com/support"
        assert contact_info.contact_message == (
            "Please contact the FirstVoices team if you have any suggestions or "
            "feedback regarding our language content."
        )

    @pytest.mark.django_db
    def test_default_values_inactive_organization(self):
        site = factories.SiteFactory(visibility=factories.Visibility.PUBLIC)
        contact_info = ContactInfo.objects.create(
            site=site, organization_status=OrganizationStatus.INACTIVE
        )
        contact_info.save()

        assert contact_info.emails[0] == "ltp@fpcc.ca"
        assert contact_info.url_list[0] == "https://www.firstvoices.com/support"
        assert contact_info.contact_message == (
            f"The project for the {site.title} language is currently inactive. "
            f"If this is your language or community and you are interested in working on this "
            f"project, please contact ltp@fpcc.ca for more information."
        )


class TestTeamMemberModel:
    @pytest.mark.django_db
    def test_representation(self):
        site = factories.SiteFactory(visibility=factories.Visibility.PUBLIC)
        organization_info = factories.ContactInfoFactory(site=site)

        team_member = factories.TeamMemberFactory(
            site=site, organization_info=organization_info
        )

        expected_str = (
            f"{team_member.name} ({site.title} - {organization_info.organization_name})"
        )
        assert str(team_member) == expected_str
