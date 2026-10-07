import csv
import logging
import os
from collections import defaultdict

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from backend.models.media import ImageFile

# ImageFile is pointed at by seven fields, not one. Only Image.original carries
# related_name="image", so filtering on that alone would treat every thumbnail in the
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

# Video.write_thumbnail_file() passes the computed width to ffmpeg and lets it work the height
# out again, so a video thumbnail can land a pixel or two over the size it was made for. The
# Image path uses PIL's thumbnail(), which always fits inside the box.
THUMBNAIL_SIZE_TOLERANCE = 2

# how many records to re-check per query before deleting
RECHECK_CHUNK_SIZE = 500

# groups an orphaned file can fall into. only APP_THUMBNAIL is deleted
APP_THUMBNAIL = "app_thumbnail"
NEEDS_REVIEW_SIZE = "needs_review_wrong_size"
NEEDS_REVIEW_INCOMPLETE = "needs_review_incomplete_set"
UPLOADED_IMAGE = "uploaded_image_file"

KEPT_GROUPS = [NEEDS_REVIEW_SIZE, NEEDS_REVIEW_INCOMPLETE, UPLOADED_IMAGE]

DELETED = "deleted"
WOULD_DELETE = "would delete"
KEPT = "kept"

# file names are deliberately left out, they can hold language words or people's names.
# media_model and title are left empty for whoever reviews the kept files to fill in.
CHANGE_LOG_FIELDNAMES = [
    "model",
    "id",
    "site",
    "created",
    "size",
    "width",
    "height",
    "group",
    "action",
    "media_model",
    "title",
]


class Command(BaseCommand):
    help = (
        "Deletes orphaned ImageFile records that the app generated as a complete set of "
        "thumbnails. Partial sets, single files and photos someone uploaded are counted and "
        "written to the change log but left in place. Use --dry-run first."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.change_log = []

    def write(self, message):
        # the project's console log handler is set to WARNING, so logging alone would be silent
        self.stdout.write(message)
        self.logger.info(message)

    def add_arguments(self, parser):
        parser.add_argument(
            "--output-dir",
            dest="output_dir",
            help="Directory to save the change log CSV file (default is current directory).",
            default=".",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            help="If set, the command will only log the changes that would be made without actually making them.",
            default=False,
        )
        parser.add_argument(
            "--sites",
            dest="site_slugs",
            help="Site slugs to limit the run to, separated by commas (optional).",
            default=None,
        )

    def validate_output_dir(self, output_dir):
        output_dir = os.path.expandvars(os.path.expanduser(output_dir))
        if not os.path.isdir(output_dir) or not os.access(output_dir, os.W_OK):
            self.logger.error(
                f"Output directory '{output_dir}' does not exist or is not writeable."
            )
            return None
        return output_dir

    # identifying generated thumbnails

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

    def is_a_plausible_size(self, image_file, size_name, max_size):
        # get_output_dimensions() never scales up, so a generated thumbnail cannot be bigger than the
        # size it was made for. rules out a large upload sharing the naming, not a small one.
        largest_side = max(image_file.width or 0, image_file.height or 0)
        if largest_side and largest_side <= max_size + THUMBNAIL_SIZE_TOLERANCE:
            return True
        self.logger.warning(
            f"[{image_file.id}] is named like a '{size_name}' thumbnail but is "
            f"{image_file.width}x{image_file.height}. Keeping it for review."
        )
        return False

    def group_image_files(self, queryset):
        # a set is only deleted when every configured size is orphaned together and each one passes the
        # size guard, a partial set may have lost a size to an earlier failed delete, and a single file
        # may just be an upload that happens to share the naming, so neither is deleted. holding one
        # size back for its dimensions holds the rest of its set back too.
        grouped = {group: [] for group in [APP_THUMBNAIL] + KEPT_GROUPS}
        candidates = []

        for instance in queryset.select_related("site").iterator(chunk_size=1000):
            details = self.get_thumbnail_details(instance.content.name)
            if details is None:
                grouped[UPLOADED_IMAGE].append(instance)
                continue
            size_name, max_size, stem = details
            if not self.is_a_plausible_size(instance, size_name, max_size):
                grouped[NEEDS_REVIEW_SIZE].append(instance)
                continue
            candidates.append((instance, size_name, stem))

        # only sizes that got this far count towards a complete set
        sizes_per_stem = defaultdict(set)
        for instance, size_name, stem in candidates:
            sizes_per_stem[(instance.site_id, stem)].add(size_name)

        size_count = len(settings.IMAGE_SIZES)
        for instance, size_name, stem in candidates:
            found = len(sizes_per_stem[(instance.site_id, stem)])
            if found < size_count:
                self.logger.warning(
                    f"[{instance.id}] is named like a '{size_name}' thumbnail but only {found} of "
                    f"{size_count} sizes from its set are orphaned and usable. Keeping it for "
                    f"review."
                )
                grouped[NEEDS_REVIEW_INCOMPLETE].append(instance)
            else:
                grouped[APP_THUMBNAIL].append(instance)

        return grouped

    # reporting

    @staticmethod
    def get_change_log_row(instance, group, action):
        return {
            "model": instance.__class__.__name__,
            "id": str(instance.id),
            "site": instance.site.slug,
            "created": instance.created.isoformat(),
            "size": instance.size,
            "width": instance.width,
            "height": instance.height,
            "group": group,
            "action": action,
            "media_model": "",
            "title": "",
        }

    def log_counts(self, grouped):
        thumbnails = grouped[APP_THUMBNAIL]
        size_count = len(settings.IMAGE_SIZES)
        total = len(thumbnails) + sum(len(grouped[group]) for group in KEPT_GROUPS)

        self.write(f"Orphaned ImageFile records: {total}")
        self.write(
            f"  complete sets of {size_count} thumbnails generated by the app: "
            f"{len(thumbnails)} ({len(thumbnails) // size_count} sets)"
        )
        self.write(
            f"  named like a thumbnail but the wrong size for one: {len(grouped[NEEDS_REVIEW_SIZE])}"
        )
        self.write(
            f"  named like a thumbnail but not a complete set: {len(grouped[NEEDS_REVIEW_INCOMPLETE])}"
        )
        self.write(f"  uploaded image files: {len(grouped[UPLOADED_IMAGE])}")
        self.write(
            f"Only the {len(thumbnails)} thumbnail(s) in a complete set will be deleted. "
            f"Everything else is written to the change log and left in place."
        )

    def record_kept_files(self, grouped):
        for group in KEPT_GROUPS:
            for instance in grouped[group]:
                self.change_log.append(self.get_change_log_row(instance, group, KEPT))

    # deleting

    @staticmethod
    def get_still_orphaned_ids(thumbnails):
        # re-checks in chunks rather than one query per record. the check is here to catch anything that
        # gained a media record since the report was read, so chunked is as good as per record.
        ids = [instance.id for instance in thumbnails]
        still_orphaned = set()
        for start in range(0, len(ids), RECHECK_CHUNK_SIZE):
            end = start + RECHECK_CHUNK_SIZE
            still_orphaned.update(
                ImageFile.objects.filter(
                    id__in=ids[start:end], **ORPHANED_IMAGE_FILE
                ).values_list("id", flat=True)
            )
        return still_orphaned

    def delete_thumbnails(self, thumbnails, dry_run):
        # deletes one record at a time. a queryset delete would skip FileBase.delete() and leave the
        # files behind in S3, no transaction around the loop on purpose: FileBase.delete() removes the S3
        # object after the row, so a rollback partway through would restore rows whose files are already
        # gone. one at a time menas a failed run can simply be re-run.
        if dry_run:
            for instance in thumbnails:
                self.change_log.append(
                    self.get_change_log_row(instance, APP_THUMBNAIL, WOULD_DELETE)
                )
            return

        still_orphaned = self.get_still_orphaned_ids(thumbnails)
        for instance in thumbnails:
            if instance.id not in still_orphaned:
                self.write(
                    f"[{instance.id}] is no longer orphaned. Leaving it in place."
                )
                continue

            self.change_log.append(
                self.get_change_log_row(instance, APP_THUMBNAIL, DELETED)
            )
            instance.delete()

    def output_change_log(self, output_dir):
        log_filename = f"delete_orphaned_thumbnail_files_log_{timezone.now().strftime('%Y%m%d_%H%M')}.csv"
        log_file = os.path.join(output_dir, log_filename)
        with open(log_file, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=CHANGE_LOG_FIELDNAMES)
            writer.writeheader()
            for change in self.change_log:
                writer.writerow(change)
        self.write(f"Change log written to {log_file}.")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        output_dir = self.validate_output_dir(options["output_dir"])
        if output_dir is None:
            return

        site_slugs = []
        if options.get("site_slugs"):
            site_slugs = [slug.strip() for slug in options["site_slugs"].split(",")]
        site_filter = {"site__slug__in": site_slugs} if site_slugs else {}

        self.write("Starting to delete orphaned thumbnail files.")
        self.write(
            f"Environment: {settings.ENVIRONMENT_NAME}. "
            f"Scope: {', '.join(site_slugs) if site_slugs else 'all sites'}."
        )
        if dry_run:
            self.write("Dry run mode enabled. No changes will be made.")

        grouped = self.group_image_files(
            ImageFile.objects.filter(**ORPHANED_IMAGE_FILE, **site_filter)
        )

        self.log_counts(grouped)
        self.record_kept_files(grouped)
        self.delete_thumbnails(grouped[APP_THUMBNAIL], dry_run)

        if self.change_log:
            self.output_change_log(output_dir)
        self.write("Finished deleting orphaned thumbnail files.")
