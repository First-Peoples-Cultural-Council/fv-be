import pytest
from django.core.management import call_command

from backend.models import Category
from backend.models.dictionary import DictionaryEntryCategory
from backend.tests import factories


@pytest.mark.django_db
class TestMergeDuplicateCategories:
    # Not one of the default categories added to every new site
    TITLE = "Test category"
    PHRASES_TITLE = "Test category (phrases)"

    def setup_method(self):
        self.site = factories.SiteFactory()

    def setup_pair(self, target_title=TITLE):
        target = factories.CategoryFactory(
            site=self.site, title=target_title, description=""
        )
        source = factories.CategoryFactory(
            site=self.site, title=self.PHRASES_TITLE, description=""
        )
        return target, source

    def add_entry(self, category):
        entry = factories.DictionaryEntryFactory(site=self.site)
        factories.DictionaryEntryCategoryFactory(
            dictionary_entry=entry, category=category
        )
        return entry

    @staticmethod
    def entry_ids(category):
        return set(
            DictionaryEntryCategory.objects.filter(category=category).values_list(
                "dictionary_entry_id", flat=True
            )
        )

    @staticmethod
    def assert_caplog_text(caplog, site_slug):
        assert (
            f"Starting to merge duplicate categories for site '{site_slug}'."
            in caplog.text
        )
        assert (
            f"Finished merging duplicate categories for site '{site_slug}'."
            in caplog.text
        )

    def test_invalid_site(self, tmp_path, caplog):
        call_command(
            "merge_duplicate_categories", site_slug="invalid", output_dir=str(tmp_path)
        )
        assert "Site with slug 'invalid' does not exist." in caplog.text

    def test_invalid_output_dir(self, caplog):
        call_command(
            "merge_duplicate_categories",
            site_slug=self.site.slug,
            output_dir="invalid/dir",
        )
        assert (
            "Output directory 'invalid/dir' does not exist or is not writeable."
            in caplog.text
        )

    def test_merge_phrases_category(self, tmp_path, caplog):
        target, source = self.setup_pair()
        word = self.add_entry(target)
        phrase = self.add_entry(source)

        call_command(
            "merge_duplicate_categories",
            site_slug=self.site.slug,
            output_dir=str(tmp_path),
        )

        assert not Category.objects.filter(id=source.id).exists()
        assert self.entry_ids(target) == {word.id, phrase.id}
        assert "Merged 1 categories" in caplog.text
        assert "Change log written to" in caplog.text
        self.assert_caplog_text(caplog, self.site.slug)

    def test_target_takes_description(self, tmp_path):
        target, source = self.setup_pair()
        source.description = "Phrases description"
        source.save()

        call_command(
            "merge_duplicate_categories",
            site_slug=self.site.slug,
            output_dir=str(tmp_path),
        )

        target.refresh_from_db()
        assert target.description == "Phrases description"

    def test_target_keeps_own_description(self, tmp_path):
        target, source = self.setup_pair()
        target.description = "Words description"
        target.save()
        source.description = "Phrases description"
        source.save()

        call_command(
            "merge_duplicate_categories",
            site_slug=self.site.slug,
            output_dir=str(tmp_path),
        )

        target.refresh_from_db()
        assert target.description == "Words description"

    def test_phrases_category_without_match_unchanged(self, tmp_path):
        lone = factories.CategoryFactory(site=self.site, title=self.PHRASES_TITLE)
        entry = self.add_entry(lone)

        call_command(
            "merge_duplicate_categories",
            site_slug=self.site.slug,
            output_dir=str(tmp_path),
        )

        lone.refresh_from_db()
        assert lone.title == self.PHRASES_TITLE
        assert self.entry_ids(lone) == {entry.id}

    def test_different_case_not_merged(self, tmp_path):
        target, source = self.setup_pair(target_title=self.TITLE.lower())

        call_command(
            "merge_duplicate_categories",
            site_slug=self.site.slug,
            output_dir=str(tmp_path),
        )

        assert Category.objects.filter(id=source.id).exists()
        assert Category.objects.filter(id=target.id).exists()

    def test_merge_into_title_with_extra_space(self, tmp_path):
        target, source = self.setup_pair(target_title=f"{self.TITLE} ")

        call_command(
            "merge_duplicate_categories",
            site_slug=self.site.slug,
            output_dir=str(tmp_path),
        )

        target.refresh_from_db()
        assert not Category.objects.filter(id=source.id).exists()
        assert target.title == self.TITLE

    def test_clean_up_titles(self, tmp_path, caplog):
        category = factories.CategoryFactory(site=self.site, title=" Test  title ")

        call_command(
            "merge_duplicate_categories",
            site_slug=self.site.slug,
            output_dir=str(tmp_path),
        )

        category.refresh_from_db()
        assert category.title == "Test title"
        assert "Cleaned up 1 category titles" in caplog.text

    def test_other_sites_unchanged(self, tmp_path):
        self.setup_pair()
        other_site = factories.SiteFactory()
        other_source = factories.CategoryFactory(
            site=other_site, title=self.PHRASES_TITLE
        )
        factories.CategoryFactory(site=other_site, title=self.TITLE)
        other_untrimmed = factories.CategoryFactory(
            site=other_site, title=f"{self.TITLE} "
        )

        call_command(
            "merge_duplicate_categories",
            site_slug=self.site.slug,
            output_dir=str(tmp_path),
        )

        other_untrimmed.refresh_from_db()
        assert Category.objects.filter(id=other_source.id).exists()
        assert other_untrimmed.title == f"{self.TITLE} "

    def test_dry_run(self, tmp_path, caplog):
        target, source = self.setup_pair()
        phrase = self.add_entry(source)
        untrimmed = factories.CategoryFactory(site=self.site, title="Test title ")

        call_command(
            "merge_duplicate_categories",
            site_slug=self.site.slug,
            output_dir=str(tmp_path),
            dry_run=True,
        )

        untrimmed.refresh_from_db()
        assert Category.objects.filter(id=source.id).exists()
        assert self.entry_ids(source) == {phrase.id}
        assert untrimmed.title == "Test title "
        assert "Dry run mode enabled. No changes will be made." in caplog.text
        assert (
            f"[Dry Run] Would merge category {source.id} into {target.id}."
            in caplog.text
        )
        assert list(tmp_path.glob("dry_run_merge_duplicate_categories_log_*.csv"))
        self.assert_caplog_text(caplog, self.site.slug)
