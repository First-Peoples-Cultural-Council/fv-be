import pytest
from django.core.management import call_command

from backend.models import Organization
from backend.tests import factories


@pytest.mark.django_db
class TestMigrateOrganizationData:

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
                key="url",
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
        assert {"contact_email_old": "test_old@fpcc.ca"} in organization.emails
        assert {"contact_email_1": "test@fpcc.ca"} in organization.emails
        assert {"contact_email_2": "test2@fpcc.ca"} in organization.emails

        assert organization.address == f"Address 1 for site {site.slug}"
        assert organization.contact_message == f"Contact message 1 for site {site.slug}"
        assert organization.url_list == [
            {"url_1": f"https://example.com/{site.slug}/url1"}
        ]

    def test_migrate_organization_data_no_contact_us_widgets(self, caplog):
        site = factories.SiteFactory.create(
            contact_email_old="test_old@fpcc.ca",
            contact_emails=["test@fpcc.ca", "test2@fpcc.ca"],
        )

        call_command("migrate_organization_data", site_slugs=site.slug)

        self.assert_caplog_text(caplog, [site.slug])
        organization = Organization.objects.get(site=site)
        assert {"contact_email_old": "test_old@fpcc.ca"} in organization.emails
        assert {"contact_email_1": "test@fpcc.ca"} in organization.emails
        assert {"contact_email_2": "test2@fpcc.ca"} in organization.emails

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
        assert organization.emails == []

        assert organization.address == f"Address 1 for site {site.slug}"
        assert organization.contact_message == f"Contact message 1 for site {site.slug}"
        assert organization.url_list == [
            {"url_1": f"https://example.com/{site.slug}/url1"}
        ]

    def test_migrate_organization_data_dry_run(self, caplog):
        site = factories.SiteFactory.create(
            contact_email_old="test_old@fpcc.ca",
            contact_emails=["test@fpcc.ca", "test2@fpcc.ca"],
            slug="test-site",
        )
        self.setup_contact_us_widgets(site)

        call_command("migrate_organization_data", site_slugs=site.slug, dry_run=True)

        self.assert_dry_run_caplog_text(caplog, [site.slug])

        dry_run_message = (
            f"Dry run: Would migrate organization data for site '{site.slug}':"
            "  Emails: [{'contact_email_old': 'test_old@fpcc.ca'}, {'contact_email_1': 'test@fpcc.ca'}, "
            "{'contact_email_2': 'test2@fpcc.ca'}]"
            f"  Addresses: Address 1 for site {site.slug}"
            f"  Contact Messages: Contact message 1 for site {site.slug}"
            "  URLs: [{'url_1': 'https://example.com/test-site/url1'}]"
        )

        assert dry_run_message in caplog.text

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
            assert {"contact_email_old": "test_old@fpcc.ca"} in organization.emails
            assert {"contact_email_1": "test@fpcc.ca"} in organization.emails
            assert {"contact_email_2": "test2@fpcc.ca"} in organization.emails

            assert organization.address == f"Address 1 for site {site.slug}"
            assert (
                organization.contact_message
                == f"Contact message 1 for site {site.slug}"
            )
            assert organization.url_list == [
                {"url_1": f"https://example.com/{site.slug}/url1"}
            ]
