from unittest.mock import patch

import pytest
from django.core.management import call_command

from backend.models.media import Image, ImageFile
from backend.tests import factories
from backend.tests.utils import get_sample_file


class TestConvertHEIC:
    SAMPLE_FILETYPE = "image/heic"
    SAMPLE_FILENAME = "sample-image.heic"
    JPG_FILENAME = "sample-image.jpg"
    JPG_FILETYPE = "image/jpeg"
    SAMPLE_FILENAME_TRANSPARENT = "sample-image-transparent.heic"
    IMAGE_TITLE = "HEIC Image"

    def create_heic_image_model(self, site, title, transparent=False):
        if transparent:
            sample_filename = self.SAMPLE_FILENAME_TRANSPARENT
        else:
            sample_filename = self.SAMPLE_FILENAME

        heic = ImageFile.objects.create(
            content=get_sample_file(sample_filename, self.SAMPLE_FILETYPE),
            site=site,
        )
        return factories.ImageFactory.create(original=heic, site=site, title=title)

    def create_jpg_image_model(self, site, title):
        jpg = ImageFile.objects.create(
            content=get_sample_file(self.JPG_FILENAME, self.JPG_FILETYPE),
            site=site,
        )
        return factories.ImageFactory.create(original=jpg, site=site, title=title)

    @staticmethod
    def confirm_model_data(original_model, converted_image_model):
        assert original_model.created_by == converted_image_model.created_by
        assert original_model.created == converted_image_model.created
        assert original_model.last_modified_by == converted_image_model.last_modified_by
        assert original_model.last_modified == converted_image_model.last_modified
        assert original_model.site == converted_image_model.site
        assert original_model.title == converted_image_model.title
        assert original_model.description == converted_image_model.description
        assert original_model.acknowledgement == converted_image_model.acknowledgement
        assert (
            original_model.exclude_from_games
            == converted_image_model.exclude_from_games
        )
        assert (
            original_model.exclude_from_kids == converted_image_model.exclude_from_kids
        )

    @staticmethod
    def confirm_image_thumbnail_data(converted_image):
        converted_image.refresh_from_db()
        assert converted_image.thumbnail.content.name.endswith(".jpg")
        assert converted_image.thumbnail.mimetype == "image/jpeg"
        assert converted_image.small.content.name.endswith(".jpg")
        assert converted_image.small.mimetype == "image/jpeg"
        assert converted_image.medium.content.name.endswith(".jpg")
        assert converted_image.medium.mimetype == "image/jpeg"

    @pytest.mark.django_db
    def test_convert_heic_image_models_invalid_sites(self, caplog):
        call_command("convert_heic", site_slugs="invalid-site")
        assert "No sites with the provided slug(s) found." in caplog.text

    @pytest.mark.django_db
    def test_convert_heic_image_models_no_heic_content(self, caplog):
        site = factories.SiteFactory.create()
        factories.ImageFactory.create(site=site)

        call_command("convert_heic", site_slugs=site.slug)

        assert "Converting HEIC files to JPEG/PNG for 1 sites." in caplog.text
        assert f"No HEIC images found for site {site.slug}" in caplog.text
        assert "HEIC to JPEG/PNG conversion completed." in caplog.text

    @pytest.mark.django_db
    @pytest.mark.disable_thumbnail_mocks
    def test_convert_heic_image_models_single_site(self, caplog):
        site = factories.SiteFactory.create()
        heic_image = self.create_heic_image_model(site, self.IMAGE_TITLE)

        assert Image.objects.filter(site=site).count() == 1

        call_command("convert_heic", site_slugs=site.slug)

        assert Image.objects.filter(site=site).count() == 1

        # 3 image thumbnails are created + 1 original image
        assert ImageFile.objects.filter(site=site).count() == 4

        converted_image = Image.objects.filter(site=site).first()

        self.confirm_model_data(heic_image, converted_image)
        assert converted_image.original.content.name.endswith(".jpg")
        assert converted_image.original.mimetype == "image/jpeg"

        self.confirm_image_thumbnail_data(converted_image)

        assert "Converting HEIC files to JPEG/PNG for 1 sites." in caplog.text
        assert "HEIC to JPEG/PNG conversion completed." in caplog.text

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "extension",
        [
            ".heic",
            ".HEIC",
            ".HeIc",
            ".heIC",
        ],
    )
    def test_convert_heic_image_case_insensitive_filename(self, caplog, extension):
        site = factories.SiteFactory.create()
        heic_image = self.create_heic_image_model(site, self.IMAGE_TITLE)

        name = "sample-image" + extension

        with patch.object(heic_image.original.content, "name", name):
            call_command("convert_heic", site_slugs=site.slug)

        converted_image = Image.objects.filter(site=site).first()

        self.confirm_model_data(heic_image, converted_image)
        assert converted_image.original.content.name.endswith(".jpg")
        assert converted_image.original.mimetype == "image/jpeg"

    @pytest.mark.django_db
    @pytest.mark.disable_thumbnail_mocks
    def test_convert_heic_image_models_single_site_transparent(self, caplog):
        site = factories.SiteFactory.create()
        heic_image = self.create_heic_image_model(
            site, self.IMAGE_TITLE, transparent=True
        )

        assert Image.objects.filter(site=site).count() == 1

        call_command("convert_heic", site_slugs=site.slug)

        assert Image.objects.filter(site=site).count() == 1

        # 3 image thumbnails are created + 1 original image
        assert ImageFile.objects.filter(site=site).count() == 4

        converted_image = Image.objects.filter(site=site).first()

        self.confirm_model_data(heic_image, converted_image)
        assert converted_image.original.content.name.endswith(".png")
        assert converted_image.original.mimetype == "image/png"

        self.confirm_image_thumbnail_data(converted_image)

        assert "Converting HEIC files to JPEG/PNG for 1 sites." in caplog.text
        assert "HEIC to JPEG/PNG conversion completed." in caplog.text

    @pytest.mark.django_db
    @pytest.mark.disable_thumbnail_mocks
    def test_convert_heic_image_models_multiple_sites(self, caplog):
        site1 = factories.SiteFactory.create()
        site2 = factories.SiteFactory.create()
        heic_image1 = self.create_heic_image_model(site1, self.IMAGE_TITLE)
        heic_image2 = self.create_heic_image_model(
            site2, self.IMAGE_TITLE, transparent=True
        )

        assert Image.objects.filter(site=site1).count() == 1
        assert Image.objects.filter(site=site2).count() == 1

        call_command("convert_heic")

        assert Image.objects.filter(site=site1).count() == 1
        assert Image.objects.filter(site=site2).count() == 1

        # 3 image thumbnails are created + 1 original image
        assert ImageFile.objects.filter(site=site1).count() == 4
        assert ImageFile.objects.filter(site=site2).count() == 4

        converted_image1 = Image.objects.filter(site=site1).first()
        converted_image2 = Image.objects.filter(site=site2).first()

        self.confirm_model_data(heic_image1, converted_image1)
        self.confirm_model_data(heic_image2, converted_image2)
        assert converted_image1.original.content.name.endswith(".jpg")
        assert converted_image1.original.mimetype == "image/jpeg"
        assert converted_image2.original.content.name.endswith(".png")
        assert converted_image2.original.mimetype == "image/png"

        self.confirm_image_thumbnail_data(converted_image1)
        self.confirm_image_thumbnail_data(converted_image2)

        assert "Converting HEIC files to JPEG/PNG for 2 sites." in caplog.text
        assert "HEIC to JPEG/PNG conversion completed." in caplog.text

    @pytest.mark.django_db
    def test_convert_heic_error_handling(self, caplog):
        site = factories.SiteFactory.create()
        self.create_heic_image_model(site, self.IMAGE_TITLE)

        assert Image.objects.filter(site=site).count() == 1

        with patch(
            "backend.management.commands.convert_heic.Command.convert_heic_to_jpeg"
        ) as mock_convert:
            mock_convert.side_effect = Exception("Conversion error")

            call_command("convert_heic", site_slugs=site.slug)

            assert "Conversion error" in caplog.text
            assert Image.objects.filter(site=site).count() == 1
            assert ImageFile.objects.filter(site=site).count() == 1

    @pytest.mark.django_db
    def test_renamed_images_converted(self, caplog):
        site = factories.SiteFactory.create()
        image_to_rename = self.create_jpg_image_model(site, self.IMAGE_TITLE)

        # Rename the image file
        image_to_rename.original.content.name = "image.HEIC"

        call_command("convert_heic", site_slugs=site.slug)

        converted_image = Image.objects.filter(site=site).first()

        assert converted_image.original.content.name.endswith(".jpg")
        assert converted_image.original.mimetype == self.JPG_FILETYPE

    @pytest.mark.django_db
    def test_log_orphaned_heic_images(self, caplog):
        site = factories.SiteFactory.create()
        heic = ImageFile.objects.create(
            content=get_sample_file(self.SAMPLE_FILENAME, self.SAMPLE_FILETYPE),
            site=site,
        )

        call_command("convert_heic", site_slugs=site.slug)

        assert (
            f"The following orphaned HEIC images were found for site {site.slug}, "
            f"and not converted:\n"
        ) in caplog.text
        assert f"- {heic.id}: {heic.content.name}" in caplog.text
