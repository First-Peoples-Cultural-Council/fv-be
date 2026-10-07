import logging

import pytest
from django.core.management import call_command

from backend.models.media import ImageFile
from backend.tests import factories

COMMAND = "report_orphaned_image_files"


@pytest.mark.django_db
class TestReportOrphanedImageFiles:
    @pytest.fixture(autouse=True)
    def capture_info_logs(self, caplog):
        # the project's log config filters INFO, so caplog needs the level lowering
        caplog.set_level(logging.INFO)

    def setup_method(self):
        self.site = factories.SiteFactory()

    def create_image_file(self, file_name, site=None, width=100, height=100):
        """
        Creates an ImageFile with a set file name and dimensions. Uses a queryset update because
        FileBase.save() refuses edits to files that already exist. The factory image is 100x100,
        which is within every configured thumbnail size.
        """
        site = site or self.site
        image_file = factories.ImageFileFactory.create(site=site)
        ImageFile.objects.filter(id=image_file.id).update(
            content=f"{site.slug}/{file_name}", width=width, height=height
        )
        return image_file

    def create_thumbnail_set(self, stem, site=None):
        return [
            self.create_image_file(f"{stem}_{size_name}.jpg", site=site)
            for size_name in ["thumbnail", "small", "medium"]
        ]

    @staticmethod
    def assert_counts(caplog, orphaned, thumbnails, photos):
        assert f"ImageFile orphaned: {orphaned} " in caplog.text
        assert f"thumbnails made by the app: {thumbnails} " in caplog.text
        assert f"uploaded photos: {photos} " in caplog.text

    def test_no_orphans(self, caplog):
        factories.ImageFactory.create(site=self.site)
        factories.VideoFactory.create(site=self.site)

        call_command(COMMAND)

        self.assert_counts(caplog, 0, 0, 0)
        assert "Finished orphaned image file report." in caplog.text

    def test_unreferenced_files_are_reported(self, caplog):
        factories.ImageFileFactory.create(site=self.site)

        call_command(COMMAND)

        self.assert_counts(caplog, 1, 0, 1)

    def test_thumbnails_attached_to_an_image_are_not_orphaned(self, caplog):
        """
        ImageFile is referenced by thumbnail, small and medium as well as original, and only
        original carries related_name="image". Guards against those being reported as orphans.
        """
        factories.ImageFactory.create(
            site=self.site,
            thumbnail=factories.ImageFileFactory.create(site=self.site),
            small=factories.ImageFileFactory.create(site=self.site),
            medium=factories.ImageFileFactory.create(site=self.site),
        )

        call_command(COMMAND)

        assert ImageFile.objects.count() == 4
        self.assert_counts(caplog, 0, 0, 0)

    def test_thumbnails_attached_to_a_video_are_not_orphaned(self, caplog):
        factories.VideoFactory.create(
            site=self.site,
            thumbnail=factories.ImageFileFactory.create(site=self.site),
        )

        call_command(COMMAND)

        self.assert_counts(caplog, 0, 0, 0)

    def test_thumbnails_and_photos_are_split_by_file_name(self, caplog):
        self.create_thumbnail_set("photo")
        self.create_image_file("photo.png")

        call_command(COMMAND)

        self.assert_counts(caplog, 4, 3, 1)

    def test_complete_set_is_reported_as_safe_to_delete(self, caplog):
        self.create_thumbnail_set("photo")

        call_command(COMMAND)

        assert "in a complete set of 3, safe to delete: 3 (1 sets" in caplog.text
        assert "in a partial set: 0" in caplog.text
        assert "on their own: 0" in caplog.text

    def test_partial_set_is_not_safe_to_delete(self, caplog):
        self.create_image_file("photo_small.jpg")
        self.create_image_file("photo_medium.jpg")

        call_command(COMMAND)

        assert "safe to delete: 0 (0 sets" in caplog.text
        assert "in a partial set: 2" in caplog.text
        assert "wrong size to be a thumbnail: 0" in caplog.text

    def test_lone_thumbnail_is_reported_on_its_own(self, caplog):
        self.create_image_file("sunset_small.jpg")

        call_command(COMMAND)

        assert "safe to delete: 0 (0 sets" in caplog.text
        assert "on their own: 1" in caplog.text

    def test_sets_on_different_sites_are_not_treated_as_one_set(self, caplog):
        other_site = factories.SiteFactory()
        self.create_image_file("photo_small.jpg")
        self.create_image_file("photo_medium.jpg", site=other_site)

        call_command(COMMAND)

        assert "on their own: 2" in caplog.text

    def test_site_breakdown(self, caplog):
        other_site = factories.SiteFactory()
        self.create_thumbnail_set("photo")
        factories.ImageFileFactory.create(site=other_site)

        call_command(COMMAND)

        assert (
            f"{self.site.slug}: total=3 thumbs=3 sets=1 lone=0 photos=0" in caplog.text
        )
        assert (
            f"{other_site.slug}: total=1 thumbs=0 sets=0 lone=0 photos=1" in caplog.text
        )

    def test_live_image_count_is_reported_per_site(self, caplog):
        factories.ImageFactory.create(site=self.site)
        factories.ImageFileFactory.create(site=self.site)

        call_command(COMMAND)

        assert "live=1" in caplog.text

    def test_sites_argument_limits_the_report(self, caplog):
        other_site = factories.SiteFactory()
        factories.ImageFileFactory.create(site=self.site)
        factories.ImageFileFactory.create(site=other_site)

        call_command(COMMAND, site_slugs=self.site.slug)

        self.assert_counts(caplog, 1, 0, 1)
        assert f"Scope: {self.site.slug}." in caplog.text

    def test_invalid_output_dir(self, caplog):
        call_command(COMMAND, output_dir="invalid/dir")

        assert (
            "Output directory 'invalid/dir' does not exist or is not writeable."
            in caplog.text
        )
        assert "Starting orphaned image file report." not in caplog.text

    def test_no_csv_without_output_dir(self, caplog):
        factories.ImageFileFactory.create(site=self.site)

        call_command(COMMAND)

        assert "Report written to" not in caplog.text

    def test_csv_written_to_output_dir(self, tmp_path, caplog):
        self.create_thumbnail_set("photo")
        self.create_image_file("photo.png")

        call_command(COMMAND, output_dir=str(tmp_path))

        assert "Report written to" in caplog.text
        written = list(tmp_path.glob("orphaned_image_files_*.csv"))
        assert len(written) == 1
        contents = written[0].read_text()
        assert "model,id,site,created,size,width,height,kind,thumbnail_set" in contents
        assert "app_thumbnail,complete" in contents
        assert "uploaded_photo," in contents

    def test_csv_does_not_include_file_names(self, tmp_path):
        self.create_image_file("sensitive_name.png")

        call_command(COMMAND, output_dir=str(tmp_path))

        contents = list(tmp_path.glob("orphaned_image_files_*.csv"))[0].read_text()
        assert "sensitive_name" not in contents

    def test_wrong_size_is_reported_separately(self, caplog):
        self.create_image_file("photo_thumbnail.jpg")
        self.create_image_file("photo_small.jpg")
        self.create_image_file("photo_medium.jpg", width=1600, height=900)

        call_command(COMMAND)

        assert "wrong size to be a thumbnail: 1" in caplog.text
        # holding one size back leaves the rest of its set incomplete
        assert "safe to delete: 0 (0 sets" in caplog.text
        assert "in a partial set: 2" in caplog.text

    def test_report_does_not_change_anything(self):
        factories.ImageFactory.create(site=self.site)
        factories.ImageFileFactory.create(site=self.site)
        before = ImageFile.objects.count()

        call_command(COMMAND)

        assert ImageFile.objects.count() == before
