import csv
import logging
import os
from collections import defaultdict

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Count
from django.utils import timezone

from backend.models.media import Image, ImageFile
from backend.models.sites import SiteFeature

# ImageFile is pointed at by seven fields. Only Image.original carries
# related_name="image", so filtering on that alone would report every thumbnail in the
# database as an orphan.
ORPHANED_IMAGE_FILE = {
    "image__isnull": True,
    "image_thumbnail__isnull": True,
    "image_small__isnull": True,
    "image_medium__isnull": True,
    "video_thumbnail__isnull": True,
    "video_small__isnull": True,
    "video_medium__isnull": True,
}

CSV_FIELDNAMES = [
    "model",
    "id",
    "site",
    "created",
    "size",
    "width",
    "height",
    "kind",
    "thumbnail_set",
]

DERIVATIVE = "app_thumbnail"
UPLOADED = "uploaded_photo"

# A thumbnail set is complete when every configured size is orphaned together and each one is a
# plausible size for the thumbnail it claims to be. Only a complete set is certain to be app
# generated, and it is the only group delete_orphaned_thumbnail_files removes.
COMPLETE = "complete"
PARTIAL = "partial"
ALONE = "alone"
WRONG_SIZE = "wrong_size"

# Video.write_thumbnail_file() lets ffmpeg recompute the height, so a video thumbnail can land a
# pixel or two over the size it was made for
THUMBNAIL_SIZE_TOLERANCE = 2

# a month holding more than this share of the total is called out as a bulk event
BULK_EVENT_SHARE = 0.1

MEGABYTE = 1024 * 1024


class Command(BaseCommand):
    help = (
        "Reports Imagefile records that are not referenced by any Image or Video. Read-only."
        "Splits them into thumbnails the app generated and photos someone uploaded, and says"
        "whether each thumbnail is part of a complete set."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def write(self, message):
        # the project's console log handler is set to WARNING, so logging alone would be silent
        self.stdout.write(message)
        self.logger.info(message)

    def add_arguments(self, parser):
        parser.add_argument(
            "--sites",
            dest="site_slug",
            help="Site slugs to limit the report to, separated by commas (optional).",
            default=None,
        )
        parser.add_argument(
            "--output-dir",
            dest="output_dir",
            help="Directory to write a CSV of the orhphaned records. The summary is logged either way.",
            default=None,
        )

    # classifying

    @staticmethod
    def get_thumbnail_details(file_name):
        # generate_resized_images() builds every output name from the same stem, as
        # "{stem}_{size name}.jpg", and always writes jpeg
        base_name = os.path.basename(file_name)
        for size_name, max_size in settings.IMAGE_SIZES.items():
            suffix = f"_{size_name}.jpg"
            if base_name.endswith(suffix):
                return size_name, max_size, base_name[: -len(suffix)]
        return None

    @staticmethod
    def is_a_plausible_size(instance, max_size):
        # get_output_dimensions() never scales up, so a thumbnail is never bigger than its size
        largest_side = max(instance.width or 0, instance.height or 0)
        return (
            bool(largest_side) and largest_side <= max_size + THUMBNAIL_SIZE_TOLERANCE
        )

    def get_rows(self, queryset):
        # one pass over the orphans, grouped the same way delete_orphaned_thumbnail_files does it, so
        # the two commands always report the same numbers. the thumbnail split and the set check both
        # work off the file name, which the database cannot group on.
        records = []
        for instance in queryset.select_related("site").iterator(chunk_size=1000):
            details = self.get_thumbnail_details(instance.content.name)
            state = None
            if details is None:
                state = ""
            elif not self.is_a_plausible_size(instance, details[1]):
                state = WRONG_SIZE
            records.append((instance, details, state))

        # only sizes that could be a thumbnail count towards a complete set
        sizes_per_stem = defaultdict(set)
        for instance, details, state in records:
            if state is None:
                sizes_per_stem[(instance.site_id, details[2])].add(details[0])

        rows = []
        for instance, details, state in records:
            if state is None:
                found = len(sizes_per_stem[(instance.site_id, details[2])])
                if found >= len(settings.IMAGE_SIZES):
                    state = COMPLETE
                else:
                    state = PARTIAL if found > 1 else ALONE
            rows.append(
                {
                    "model": ImageFile.__name__,
                    "id": str(instance.id),
                    "site": instance.site.slug,
                    "created": instance.created,
                    "size": instance.size or 0,
                    "width": instance.width,
                    "height": instance.height,
                    "kind": UPLOADED if details is None else DERIVATIVE,
                    "thumbnail_set": state,
                }
            )
        return rows

    # formatting helpers

    @staticmethod
    def megabytes(rows):
        return sum(row["size"] for row in rows) / MEGABYTE

    @staticmethod
    def day(value):
        return value.strftime("%Y-%m-%d") if value else "-"

    @staticmethod
    def thumbnails(rows):
        return [row for row in rows if row["kind"] == DERIVATIVE]

    @staticmethod
    def photos(rows):
        return [row for row in rows if row["kind"] == UPLOADED]

    @staticmethod
    def in_set_state(rows, state):
        return [row for row in rows if row["thumbnail_set"] == state]

    # report sections

    def log_overview(self, rows, site_slugs):
        scope = ", ".join(site_slugs) if site_slugs else "all sites"
        self.write(f"Environment: {settings.ENVIRONMENT_NAME}. Scope: {scope}.")
        self.write(f"ImageFile records total: {ImageFile.objects.count()}")

        thumbnails = self.thumbnails(rows)
        photos = self.photos(rows)
        complete = self.in_set_state(thumbnails, COMPLETE)
        size_count = len(settings.IMAGE_SIZES)

        self.write(f"ImageFile orphaned: {len(rows)} ({self.megabytes(rows):.1f} MB)")
        self.write(
            f"   thumbnails made by the app: {len(thumbnails)} "
            f"({self.megabytes(thumbnails):.1f} MB)"
        )
        self.write(
            f"   in a complete set of {size_count}, safe to delete: {len(complete)} "
            f"({len(complete) // size_count} sets, {self.megabytes(complete):.1f} MB)"
        )
        self.write(
            f"   in a partial set: {len(self.in_set_state(thumbnails, PARTIAL))}"
        )
        self.write(f"   on their own: {len(self.in_set_state(thumbnails, ALONE))}")
        self.write(
            f"   wrong size to be a thumbnail: "
            f"{len(self.in_set_state(thumbnails, WRONG_SIZE))}"
        )
        self.write(
            f"   uploaded photos: {len(photos)} ({self.megabytes(photos):.1f} MB)"
        )

    def log_months(self, rows):
        self.write("Orphaned ImageFile records by the month the file was made:")
        counts = defaultdict(int)
        for row in rows:
            counts[row["created"].strftime("%Y-%m")] += 1
        for month in sorted(counts):
            flag = (
                " (bulk event)" if counts[month] > len(rows) * BULK_EVENT_SHARE else ""
            )
            self.write(f"   {month}: {counts[month]}{flag}")

    def log_sites(self, rows):
        by_site = defaultdict(list)
        for row in rows:
            by_site[row["site"]].append(row)

        live_images = dict(
            Image.objects.filter(site__slug__in=by_site)
            .values("site__slug")
            .annotate(count=Count("id"))
            .values_list("site__slug", "count")
        )

        self.write("Orphaned ImageFile record by site:")
        self.write(
            "   complete = thumbnails in a full set and safe to delete, "
            "partial/alone/badsize = kept for review"
        )
        for slug, site_rows in sorted(by_site.items(), key=lambda item: -len(item[1])):
            thumbnails = self.thumbnails(site_rows)
            created = [row["created"] for row in site_rows]
            self.write(
                f"   {slug}: total={len(site_rows)} thumbs={len(thumbnails)} "
                f"complete={len(self.in_set_state(thumbnails, COMPLETE))}"
                f"partial={len(self.in_set_state(thumbnails, PARTIAL))}"
                f"alone={len(self.in_set_state(thumbnails, ALONE))}"
                f"badsize={len(self.in_set_state(thumbnails, WRONG_SIZE))}"
                f"photos={len(site_rows) - len(thumbnails)} "
                f"live={live_images.get(slug, 0)} "
                f"first={self.day(min(created))} last={self.day(max(created))}"
            )
        shared = list(
            SiteFeature.objects.filter(
                key__iexact="shared_media", is_enabled=True
            ).values_list("site__slug", flat=True)
        )
        self.write(f"Sites with shared_media enabled: {shared if shared else 'none'}")

    def log_photos(self, rows):
        photos = self.photos(rows)
        if not photos:
            self.write("No orphaned uploaded photos.")
            return

        created = [row["created"] for row in photos]
        self.write("Orphaned uploaded photos, the group that needs a decision:")
        self.write(f"   count: {len(photos)}")
        self.write(
            f"   added between {self.day(min(created))} and {self.day(max(created))}"
        )
        counts = defaultdict(int)
        for row in photos:
            counts[row["site"]] += 1
        for slug in sorted(counts, key=lambda s: -counts[s]):
            self.write(f"   {slug}: {counts[slug]}")

    # csv output

    def validate_output_dir(self, output_dir):
        output_dir = os.path.expandvars(os.path.expanduser(output_dir))
        if not os.path.isdir(output_dir) or not os.access(output_dir, os.W_OK):
            self.logger.error(
                f"Output directory '{output_dir}' does not exist or is not writeable."
            )
            return None
        return output_dir

    def output_report(self, output_dir, rows):
        filename = f"orphaned_image_files_{timezone.now().strftime('%Y%m%d_%H%M')}.csv"
        report_file = os.path.join(output_dir, filename)
        with open(report_file, "w", newline="") as csvfile:
            writer = csv.DictWriter(
                csvfile, fieldnames=CSV_FIELDNAMES, extrasaction="ignore"
            )
            writer.writeheader()
            for row in rows:
                writer.writerow({**row, "created": row["created"].isoformat()})
        self.write(f"Report written to {report_file}.")

    def handle(self, *args, **options):
        output_dir = options["output_dir"]
        if output_dir is not None:
            output_dir = self.validate_output_dir(output_dir)
            if output_dir is None:
                return
        site_slugs = []
        if options.get("site_slugs"):
            site_slugs = [slug.strip() for slug in options["site_slugs"].split(",")]
        site_filter = {"site__slug__in": site_slugs} if site_slugs else {}

        self.write("Starting orphaned image file report.")

        rows = self.get_rows(
            ImageFile.objects.filter(**ORPHANED_IMAGE_FILE, **site_filter)
        )

        self.log_overview(rows, site_slugs)

        if rows:
            self.log_months(rows)
            self.log_sites(rows)
            self.log_photos(rows)

            if output_dir is not None:
                self.output_report(output_dir, rows)

        self.write("Finished orphaned image file report.")
