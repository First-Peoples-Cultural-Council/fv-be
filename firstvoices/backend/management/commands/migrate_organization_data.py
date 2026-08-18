import logging

from django.core.management.base import BaseCommand

from backend.models import Organization, Site
from backend.models.widget import SiteWidget, WidgetSettings


class Command(BaseCommand):
    help = "Migrate organization data from site models and contact info widgets."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.default_contact_message = (
            "Please contact us if you have any suggestions "
            "or feedback regarding our language content."
        )

    def add_arguments(self, parser):
        parser.add_argument(
            "--sites",
            dest="site_slugs",
            help="Slugs of sites to migrate. Note that any provided site "
            "missing an organization model will have one created.",
            default=None,
        )

        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="If set the command will only simulate a migration and return the results.",
            default=False,
        )

    @staticmethod
    def extract_data_from_widgets(contact_us_widgets):
        org_addresses = list(
            WidgetSettings.objects.filter(
                widget__in=contact_us_widgets, key="textWithFormatting"
            )
            .values_list("value", flat=True)
            .distinct()
        )
        if org_addresses:
            org_addresses = "\n".join(value for value in org_addresses if value.strip())

        org_contact_messages = list(
            WidgetSettings.objects.filter(widget__in=contact_us_widgets, key="text")
            .values_list("value", flat=True)
            .distinct()
        )
        if org_contact_messages:
            org_contact_messages = "\n".join(
                value for value in org_contact_messages if value.strip()
            )

        org_urls = []
        url_values = list(
            WidgetSettings.objects.filter(widget__in=contact_us_widgets, key="url")
            .values_list("value", flat=True)
            .distinct()
        )
        if url_values:
            for idx, value in enumerate(url_values):
                urls = value.split(",")
                for url in urls:
                    if url.strip():
                        org_urls.append({f"url_{idx}": url.strip()})

        return org_addresses, org_contact_messages, org_urls

    @staticmethod
    def extract_emails_from_site(site):
        org_emails = []
        if site.contact_email_old:
            org_emails.append({"contact_email_old": site.contact_email_old})
        if site.contact_emails:
            for idx, contact_email in enumerate(site.contact_emails):
                org_emails.append({f"contact_email_{idx}": contact_email})
        return org_emails

    def migrate_organization_data(self, site, dry_run=False):
        org_addresses = []
        org_contact_messages = []
        org_urls = []

        contact_us_widgets = SiteWidget.objects.filter(
            site=site, widget_type="WIDGET_CONTACT"
        )
        if not contact_us_widgets.exists():
            self.logger.info(
                f"No contact us widgets found for site '{site.slug}'. "
                f"Migrating data from site model email fields only."
            )
        else:
            org_addresses, org_contact_messages, org_urls = (
                self.extract_data_from_widgets(contact_us_widgets)
            )

        org_emails = self.extract_emails_from_site(site)

        if dry_run:
            self.logger.info(
                f"Dry run: Would migrate organization data for site '{site.slug}':"
                f"  Emails: {org_emails}"
                f"  Addresses: {org_addresses}"
                f"  Contact Messages: {org_contact_messages}"
                f"  URLs: {org_urls}"
            )
            return

        organization = Organization.objects.get_or_create(site=site)
        organization = organization[0]  # get the instance from the tuple

        # Don't have to worry about overwriting existing data as no sites have organization data yet.
        organization.contact_emails = org_emails
        organization.address = org_addresses if org_addresses else ""
        organization.contact_message = (
            org_contact_messages
            if org_contact_messages
            else self.default_contact_message
        )
        organization.url_list = org_urls if org_urls else []
        organization.save()
        self.logger.info(f"Organization data migrated for site '{site.slug}'.")

    def handle(self, *args, **options):
        if options.get("site_slugs"):
            site_slugs_list = options.get("site_slugs", "").split(",").strip()
            sites = Site.objects.filter(slug__in=site_slugs_list)
            if not sites:
                self.logger.warning("No sites with the provided slug(s) found.")
                return

        else:
            sites = Site.objects.all()

        for site in sites:
            if options.get("dry_run"):
                self.logger.info(f"Performing dry run for site '{site.slug}'...")
                self.migrate_organization_data(site, dry_run=True)
            else:
                self.logger.info(
                    f"Performing organization info migration for site '{site.slug}'..."
                )
                self.migrate_organization_data(site, dry_run=False)
