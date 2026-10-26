import pytest
from django.core.management import call_command

from backend.models import Organization
from backend.tests import factories
from backend.utils.uuid_utils import is_valid_uuid


@pytest.mark.django_db
class TestMigrateOrganizationData:

    @staticmethod
    def strip_ids(data):
        result = []
        for item in data:
            assert set(item) == {"id", "label", "value"}
            assert is_valid_uuid(item["id"])
            item.pop("id")
            result.append(item)
        return result

    @staticmethod
    def setup_contact_us_widgets(site, count=1):
        for x in range(count):
            widget = factories.SiteWidgetFactory.create(
                site=site,
                widget_type="WIDGET_CONTACT",
            )
            factories.WidgetSettingsFactory.create(
                widget=widget,
                key="textWithFormatting",
                value=f"Address {x + 1} for site {site.slug}",
            )
            factories.WidgetSettingsFactory.create(
                widget=widget,
                key="text",
                value=f"Contact message {x + 1} for site {site.slug}",
            )
            factories.WidgetSettingsFactory.create(
                widget=widget,
                key="urls",
                value=f"https://example.com/{site.slug}/url{x + 1}",
            )

    @staticmethod
    def assert_caplog_text(caplog, site_slugs):
        for slug in site_slugs:
            assert (
                f"Performing organization info migration for site '{slug}'..."
                in caplog.text
            )
            assert f"Organization data migrated for site '{slug}'." in caplog.text

        assert "Organization data migrated for all specified sites." in caplog.text

    @staticmethod
    def assert_dry_run_caplog_text(caplog, site_slugs):
        for slug in site_slugs:
            assert f"Performing dry run for site '{slug}'..." in caplog.text
            assert (
                f"Dry run: Would migrate organization data for site '{slug}':"
                in caplog.text
            )

        assert (
            "Dry run process completed for all specified sites. No changes were made."
            in caplog.text
        )

    def test_migrate_organization_data_no_site(self, caplog):
        call_command("migrate_organization_data", site_slugs="invalid-site")
        assert "No sites with the provided slug(s) found." in caplog.text

    def test_migrate_organization_data_single_site(self, caplog):
        site = factories.SiteFactory.create(
            contact_email_old="test_old@fpcc.ca",
            contact_emails=["test@fpcc.ca", "test2@fpcc.ca"],
        )
        self.setup_contact_us_widgets(site)

        call_command("migrate_organization_data", site_slugs=site.slug)

        self.assert_caplog_text(caplog, [site.slug])
        organization = Organization.objects.get(site=site)

        assert organization.name == f"{site.title} Language Team"
        org_emails = self.strip_ids(organization.emails)
        assert {"label": "Contact Email Old", "value": "test_old@fpcc.ca"} in org_emails
        assert {"label": "Contact Email 1", "value": "test@fpcc.ca"} in org_emails
        assert {"label": "Contact Email 2", "value": "test2@fpcc.ca"} in org_emails

        assert organization.address == f"Address 1 for site {site.slug}"
        assert organization.contact_message == f"Contact message 1 for site {site.slug}"

        org_urls = self.strip_ids(organization.url_list)
        assert {
            "label": "URL 1",
            "value": f"https://example.com/{site.slug}/url1",
        } in org_urls

    def test_migrate_organization_data_no_contact_us_widgets(self, caplog):
        site = factories.SiteFactory.create(
            contact_email_old="test_old@fpcc.ca",
            contact_emails=["test@fpcc.ca", "test2@fpcc.ca"],
        )

        call_command("migrate_organization_data", site_slugs=site.slug)

        self.assert_caplog_text(caplog, [site.slug])
        organization = Organization.objects.get(site=site)

        assert organization.name == f"{site.title} Language Team"

        org_emails = self.strip_ids(organization.emails)
        assert {"label": "Contact Email Old", "value": "test_old@fpcc.ca"} in org_emails
        assert {"label": "Contact Email 1", "value": "test@fpcc.ca"} in org_emails
        assert {"label": "Contact Email 2", "value": "test2@fpcc.ca"} in org_emails

        assert organization.address == ""
        assert organization.contact_message == (
            "Please contact us if you have any suggestions "
            "or feedback regarding our language content."
        )
        assert organization.url_list == []

    def test_migrate_organization_data_no_emails(self, caplog):
        site = factories.SiteFactory.create()
        self.setup_contact_us_widgets(site)

        call_command("migrate_organization_data", site_slugs=site.slug)

        self.assert_caplog_text(caplog, [site.slug])
        organization = Organization.objects.get(site=site)
        org_emails = self.strip_ids(organization.emails)
        assert org_emails == []

        assert organization.name == f"{site.title} Language Team"
        assert organization.address == f"Address 1 for site {site.slug}"
        assert organization.contact_message == f"Contact message 1 for site {site.slug}"

        org_urls = self.strip_ids(organization.url_list)
        assert {
            "label": "URL 1",
            "value": f"https://example.com/{site.slug}/url1",
        } in org_urls

    def test_migrate_organization_data_dry_run(self, caplog):
        site = factories.SiteFactory.create(
            contact_email_old="test_old@fpcc.ca",
            contact_emails=["test@fpcc.ca", "test2@fpcc.ca"],
            slug="test-site",
        )
        self.setup_contact_us_widgets(site)

        call_command("migrate_organization_data", site_slugs=site.slug, dry_run=True)

        self.assert_dry_run_caplog_text(caplog, [site.slug])

        assert (
            f"Dry run: Would migrate organization data for site '{site.slug}':"
            in caplog.text
        )
        assert (
            "'label': 'Contact Email Old', 'value': 'test_old@fpcc.ca'" in caplog.text
        )
        assert "'label': 'Contact Email 1', 'value': 'test@fpcc.ca'" in caplog.text
        assert "'label': 'Contact Email 2', 'value': 'test2@fpcc.ca'" in caplog.text
        assert f"  Addresses: Address 1 for site {site.slug}" in caplog.text
        assert (
            f"  Contact Messages: Contact message 1 for site {site.slug}" in caplog.text
        )
        assert (
            "'label': 'URL 1', 'value': 'https://example.com/test-site/url1'"
            in caplog.text
        )

    def test_migrate_organization_data_all_sites(self, caplog):
        site1 = factories.SiteFactory.create(
            contact_email_old="test_old@fpcc.ca",
            contact_emails=["test@fpcc.ca", "test2@fpcc.ca"],
        )
        site2 = factories.SiteFactory.create(
            contact_email_old="test_old@fpcc.ca",
            contact_emails=["test@fpcc.ca", "test2@fpcc.ca"],
        )

        self.setup_contact_us_widgets(site1)
        self.setup_contact_us_widgets(site2)

        call_command("migrate_organization_data", dry_run=False)
        self.assert_caplog_text(caplog, [site1.slug, site2.slug])

        for site in [site1, site2]:
            organization = Organization.objects.get(site=site)

            assert organization.name == f"{site.title} Language Team"
            org_emails = self.strip_ids(organization.emails)
            assert {
                "label": "Contact Email Old",
                "value": "test_old@fpcc.ca",
            } in org_emails
            assert {"label": "Contact Email 1", "value": "test@fpcc.ca"} in org_emails
            assert {"label": "Contact Email 2", "value": "test2@fpcc.ca"} in org_emails

            assert organization.address == f"Address 1 for site {site.slug}"
            assert (
                organization.contact_message
                == f"Contact message 1 for site {site.slug}"
            )
            org_urls = self.strip_ids(organization.url_list)
            assert {
                "label": "URL 1",
                "value": f"https://example.com/{site.slug}/url1",
            } in org_urls
