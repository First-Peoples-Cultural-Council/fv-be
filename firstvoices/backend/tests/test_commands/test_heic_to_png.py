import pytest
from django.core.management import call_command

from backend.models.media import Image, ImageFile
from backend.tests import factories
from backend.tests.utils import get_sample_file


class TestHEICToPNG:
    SAMPLE_FILETYPE = "image/heic"
    SAMPLE_FILENAME = "sample-image.heic"
    IMAGE_TITLE = "HEIC Image"

    def create_heic_image_model(self, site, title):
        heic = ImageFile.objects.create(
            content=get_sample_file(self.SAMPLE_FILENAME, self.SAMPLE_FILETYPE),
            site=site,
        )
        return factories.ImageFactory.create(original=heic, site=site, title=title)

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

    @pytest.mark.django_db
    def test_convert_heic_image_models_single_site(self):
        site = factories.SiteFactory.create()
        heic_image = self.create_heic_image_model(site, self.IMAGE_TITLE)

        assert Image.objects.filter(site=site).count() == 1

        call_command("heic_to_png", site_slugs=site.slug)

        assert Image.objects.filter(site=site).count() == 1
        assert ImageFile.objects.filter(site=site).count() == 1

        converted_image = Image.objects.filter(site=site).first()

        self.confirm_model_data(heic_image, converted_image)
        assert converted_image.original.content.name.endswith(".png")
        assert converted_image.original.mimetype == "image/png"

    @pytest.mark.django_db
    def test_convert_heic_image_models_multiple_sites(self):
        site1 = factories.SiteFactory.create()
        site2 = factories.SiteFactory.create()
        heic_image1 = self.create_heic_image_model(site1, self.IMAGE_TITLE)
        heic_image2 = self.create_heic_image_model(site2, self.IMAGE_TITLE)

        assert Image.objects.filter(site=site1).count() == 1
        assert Image.objects.filter(site=site2).count() == 1

        call_command("heic_to_png")

        assert Image.objects.filter(site=site1).count() == 1
        assert Image.objects.filter(site=site2).count() == 1
        assert ImageFile.objects.filter(site=site1).count() == 1
        assert ImageFile.objects.filter(site=site2).count() == 1

        converted_image1 = Image.objects.filter(site=site1).first()
        converted_image2 = Image.objects.filter(site=site2).first()

        self.confirm_model_data(heic_image1, converted_image1)
        self.confirm_model_data(heic_image2, converted_image2)
        assert converted_image1.original.content.name.endswith(".png")
        assert converted_image1.original.mimetype == "image/png"
        assert converted_image2.original.content.name.endswith(".png")
        assert converted_image2.original.mimetype == "image/png"
